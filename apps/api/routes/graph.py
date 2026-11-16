from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Dict, Any

from packages.shared.models import Project, User, Repository, RepositorySnapshot, CodeEntity, CallRelationship, Dependency
from apps.api.core.deps import get_db, get_current_user

router = APIRouter()
_GRAPH_CACHE: Dict[str, Dict[str, Any]] = {}

@router.get("/{project_id}/graph")
def get_project_graph(
    project_id: UUID, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get the latest snapshot
    snapshot = db.query(RepositorySnapshot).join(Repository).filter(Repository.project_id == project.id).order_by(RepositorySnapshot.created_at.desc()).first()
    if not snapshot:
        return {"nodes": [], "edges": []}

    cache_key = f"{snapshot.id}_{snapshot.created_at.isoformat() if snapshot.created_at else ''}"
    if cache_key in _GRAPH_CACHE:
        return _GRAPH_CACHE[cache_key]

    files = db.query(File).filter(File.snapshot_id == snapshot.id).all()
    entities = db.query(CodeEntity).filter(CodeEntity.snapshot_id == snapshot.id).all()
    calls = db.query(CallRelationship).filter(CallRelationship.snapshot_id == snapshot.id).all()
    dependencies = db.query(Dependency).filter(Dependency.snapshot_id == snapshot.id).all()

    nodes = []
    edges = []
    
    # 1. Create File and Folder nodes
    folder_set = set()
    file_map = {}
    
    for f in files:
        file_map[f.id] = f
        
        # Determine folder path
        parts = f.path.split('/')
        if len(parts) > 1:
            folder_path = '/'.join(parts[:-1])
            folder_set.add(folder_path)
            
            # Create edge from folder to file
            edges.append({
                "id": f"edge-contain-{folder_path}-{f.id}",
                "source": f"folder-{folder_path}",
                "target": f"file-{f.id}",
                "type": "containment"
            })
            
            # Ensure folder chain exists
            current_path = ""
            for i, part in enumerate(parts[:-1]):
                next_path = f"{current_path}/{part}" if current_path else part
                if current_path:
                    edges.append({
                        "id": f"edge-contain-{current_path}-{next_path}",
                        "source": f"folder-{current_path}",
                        "target": f"folder-{next_path}",
                        "type": "containment"
                    })
                current_path = next_path
                folder_set.add(current_path)

        # File Node
        nodes.append({
            "id": f"file-{f.id}",
            "type": "file",
            "data": {
                "label": f"File: {parts[-1]}",
                "name": parts[-1],
                "type": "file",
                "full_path": f.path
            }
        })

    # Folder Nodes
    for folder in folder_set:
        folder_name = folder.split('/')[-1]
        nodes.append({
            "id": f"folder-{folder}",
            "type": "folder",
            "data": {
                "label": f"Folder: {folder_name}",
                "name": folder_name,
                "type": "folder",
                "full_path": folder
            }
        })

    # 2. Entity Nodes with Centrality & Coupling Metrics
    from apps.analyzer.algorithms import compute_pagerank, compute_coupling_metrics
    call_edges = [(str(c.caller_id), str(c.callee_id)) for c in calls if c.caller_id and c.callee_id]
    entity_id_strs = [str(ent.id) for ent in entities]
    pageranks = compute_pagerank(entity_id_strs, call_edges)
    couplings = compute_coupling_metrics(entity_id_strs, call_edges)

    for ent in entities:
        node_id_str = str(ent.id)
        node_pr = pageranks.get(node_id_str, 0.0)
        node_coupling = couplings.get(node_id_str, {"ca": 0, "ce": 0, "instability": 0.0})

        nodes.append({
            "id": node_id_str,
            "type": "custom",
            "data": {
                "label": f"{ent.type}: {ent.name}",
                "name": ent.name,
                "type": ent.type,
                "pagerank": node_pr,
                "ca": node_coupling["ca"],
                "ce": node_coupling["ce"],
                "instability": node_coupling["instability"]
            }
        })
        # Link entity to its file
        if ent.file_id:
            edges.append({
                "id": f"edge-contain-file-{ent.file_id}-{ent.id}",
                "source": f"file-{ent.file_id}",
                "target": str(ent.id),
                "type": "containment"
            })

    # 3. Call Edges (Entity to Entity)
    for i, call in enumerate(calls):
        if call.caller_id and call.callee_id:
            edges.append({
                "id": f"edge-call-{call.id}",
                "source": str(call.caller_id),
                "target": str(call.callee_id),
                "type": "call"
            })

    # 4. Dependency Edges (Module Imports)
    for dep in dependencies:
        if dep.source_id and dep.target_id:
            edges.append({
                "id": f"edge-dep-{dep.id}",
                "source": str(dep.source_id),
                "target": str(dep.target_id),
                "type": "dependency",
                "label": dep.type
            })

    result = {"nodes": nodes, "edges": edges}
    if len(_GRAPH_CACHE) > 50:
        _GRAPH_CACHE.pop(next(iter(_GRAPH_CACHE)))
    _GRAPH_CACHE[cache_key] = result

    return result


import os
from packages.shared.models.code_entity import File
from packages.shared.utils.workspace import get_workspace_dir

def _is_safe_path(target_path: str, base_dir: str) -> bool:
    abs_target = os.path.abspath(target_path)
    abs_base = os.path.abspath(base_dir)
    try:
        return os.path.commonpath([abs_base, abs_target]) == abs_base
    except ValueError:
        return False

@router.get("/{project_id}/entities/{entity_id}")
def get_entity_details(
    project_id: UUID,
    entity_id: str,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get latest snapshot for project
    snapshot = db.query(RepositorySnapshot).join(Repository).filter(Repository.project_id == project.id).order_by(RepositorySnapshot.created_at.desc()).first()

    # 1. Handle Folder nodes
    if entity_id.startswith("folder-"):
        folder_path = entity_id[len("folder-"):]
        folder_name = folder_path.split("/")[-1] if "/" in folder_path else folder_path
        
        contained_files = []
        if snapshot:
            files_in_folder = db.query(File).filter(
                File.snapshot_id == snapshot.id,
                File.path.startswith(folder_path + "/")
            ).all()
            contained_files = [f.path for f in files_in_folder]

        return {
            "id": entity_id,
            "name": folder_name,
            "type": "folder",
            "file_path": folder_path,
            "start_line": None,
            "end_line": None,
            "source_code": f"# Directory: {folder_path}\n# Contains {len(contained_files)} files:\n" + "\n".join(f"#  - {p}" for p in contained_files[:20]),
            "callers": [],
            "callees": []
        }

    # 2. Handle File nodes
    if entity_id.startswith("file-"):
        raw_id = entity_id[len("file-"):]
        try:
            file_uuid = UUID(raw_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid file UUID")

        file_obj = db.query(File).filter(File.id == file_uuid).first()
        if not file_obj:
            raise HTTPException(status_code=404, detail="File not found")

        source_code = ""
        workspace_dir = get_workspace_dir(str(file_obj.snapshot_id))
        file_path = os.path.join(workspace_dir, file_obj.path)
        if _is_safe_path(file_path, workspace_dir) and os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source_code = f.read()
            except Exception:
                source_code = "# Unable to read file content"

        file_name = file_obj.path.split("/")[-1]
        
        # Entities inside this file
        file_entities = db.query(CodeEntity).filter(CodeEntity.file_id == file_obj.id).all()

        return {
            "id": entity_id,
            "name": file_name,
            "type": "file",
            "file_path": file_obj.path,
            "start_line": 1,
            "end_line": len(source_code.splitlines()) if source_code else None,
            "source_code": source_code,
            "callers": [],
            "callees": [{"id": str(e.id), "name": e.name, "type": e.type} for e in file_entities]
        }

    # 3. Handle Code Entity UUID
    try:
        parsed_entity_uuid = UUID(entity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid entity UUID")

    ent = db.query(CodeEntity).filter(CodeEntity.id == parsed_entity_uuid).first()
    if not ent:
        raise HTTPException(status_code=404, detail="Entity not found")
        
    file_obj = db.query(File).filter(File.id == ent.file_id).first()
    
    source_code = ""
    if file_obj:
        workspace_dir = get_workspace_dir(str(ent.snapshot_id))
        file_path = os.path.join(workspace_dir, file_obj.path)
        if _is_safe_path(file_path, workspace_dir) and os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if ent.start_line and ent.end_line:
                        source_code = "".join(lines[ent.start_line - 1 : ent.end_line])
                    else:
                        source_code = "".join(lines)
            except Exception:
                source_code = "# Unable to read source code snippet"
    
    # Find callers and callees
    callers = db.query(CallRelationship).filter(CallRelationship.callee_id == ent.id).all()
    callees = db.query(CallRelationship).filter(CallRelationship.caller_id == ent.id).all()
    
    caller_ids = [c.caller_id for c in callers if c.caller_id]
    callee_ids = [c.callee_id for c in callees if c.callee_id]
    
    caller_entities = db.query(CodeEntity).filter(CodeEntity.id.in_(caller_ids)).all() if caller_ids else []
    callee_entities = db.query(CodeEntity).filter(CodeEntity.id.in_(callee_ids)).all() if callee_ids else []

    return {
        "id": str(ent.id),
        "name": ent.name,
        "type": ent.type,
        "file_path": file_obj.path if file_obj else "",
        "start_line": ent.start_line,
        "end_line": ent.end_line,
        "source_code": source_code,
        "callers": [{"id": str(c.id), "name": c.name, "type": c.type} for c in caller_entities],
        "callees": [{"id": str(c.id), "name": c.name, "type": c.type} for c in callee_entities]
    }
