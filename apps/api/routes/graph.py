from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Dict, Any

from packages.shared.models import Project, User, Repository, RepositorySnapshot, CodeEntity, CallRelationship
from apps.api.core.deps import get_db, get_current_user

router = APIRouter()

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

    files = db.query(File).filter(File.snapshot_id == snapshot.id).all()
    entities = db.query(CodeEntity).filter(CodeEntity.snapshot_id == snapshot.id).all()
    calls = db.query(CallRelationship).filter(CallRelationship.snapshot_id == snapshot.id).all()

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

    # 2. Entity Nodes
    for ent in entities:
        nodes.append({
            "id": str(ent.id),
            "type": "custom",
            "data": {
                "label": f"{ent.type}: {ent.name}",
                "name": ent.name,
                "type": ent.type
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

    return {"nodes": nodes, "edges": edges}


import os
from packages.shared.models.code_entity import File
from packages.shared.utils.workspace import get_workspace_dir

@router.get("/{project_id}/entities/{entity_id}")
def get_entity_details(
    project_id: UUID,
    entity_id: UUID,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    ent = db.query(CodeEntity).filter(CodeEntity.id == entity_id).first()
    if not ent:
        raise HTTPException(status_code=404, detail="Entity not found")
        
    file_obj = db.query(File).filter(File.id == ent.file_id).first()
    
    source_code = ""
    if file_obj:
        workspace_dir = get_workspace_dir(str(ent.snapshot_id))
        file_path = os.path.join(workspace_dir, file_obj.path)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if ent.start_line and ent.end_line:
                    source_code = "".join(lines[ent.start_line - 1 : ent.end_line])
                else:
                    source_code = "".join(lines)
    
    # Also find out who calls this, and who this calls
    callers = db.query(CallRelationship).filter(CallRelationship.callee_id == ent.id).all()
    callees = db.query(CallRelationship).filter(CallRelationship.caller_id == ent.id).all()
    
    caller_ids = [str(c.caller_id) for c in callers if c.caller_id]
    callee_ids = [str(c.callee_id) for c in callees if c.callee_id]
    
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
