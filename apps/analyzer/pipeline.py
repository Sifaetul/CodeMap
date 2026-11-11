from sqlalchemy.orm import Session
from packages.shared.models import AnalysisJob, File, CodeEntity, ClassEntity, FunctionEntity, Dependency, CallRelationship
from apps.analyzer.scanner import RepositoryScanner
from apps.analyzer.parsers.python_parser import PythonParser
import os
import uuid

def run_analysis_pipeline(db: Session, snapshot_id: str, workspace_dir: str, job: AnalysisJob):
    # --- PHASE 1: SCANNING ---
    job.current_stage = "SCANNING"
    db.commit()
    
    scanner = RepositoryScanner(workspace_dir)
    files_by_ext = scanner.scan()
    
    file_records = {}
    for ext, rel_paths in files_by_ext.items():
        for rel_path in rel_paths:
            f = File(snapshot_id=uuid.UUID(snapshot_id), path=rel_path, language="python" if ext == ".py" else "unknown")
            db.add(f)
            file_records[rel_path] = f
            
    db.commit()

    # --- PHASE 2: PARSING ---
    job.current_stage = "PARSING"
    db.commit()
    
    py_parser = PythonParser()
    python_files = files_by_ext.get(".py", [])
    
    parsed_results = [] # Store for graph building
    
    for rel_path in python_files:
        abs_path = os.path.join(workspace_dir, rel_path)
        file_record = file_records[rel_path]
        
        try:
            with open(abs_path, 'r', encoding='utf-8') as f_in:
                content = f_in.read()
                
            result = py_parser.parse(content, rel_path)
            
            # Map entity names to their DB IDs for this file
            entity_id_map = {}
            
            for ent in result["entities"]:
                ce = CodeEntity(
                    snapshot_id=uuid.UUID(snapshot_id),
                    file_id=file_record.id,
                    name=ent["name"],
                    type=ent["type"],
                    start_line=ent["start_line"],
                    end_line=ent["end_line"],
                )
                db.add(ce)
                db.flush()
                entity_id_map[ent["name"]] = ce.id
                
                if ent["type"] == "class":
                    db.add(ClassEntity(id=ce.id))
                elif ent["type"] == "function":
                    db.add(FunctionEntity(id=ce.id, is_async=False))
            
            parsed_results.append({
                "file_id": file_record.id,
                "entity_id_map": entity_id_map,
                "imports": result["imports"],
                "calls": result["calls"]
            })
                    
        except Exception as e:
            print(f"Pipeline error processing {rel_path}: {e}")
            
    db.commit()
    
    
    # --- PHASE 3: GRAPH BUILDING ---
    job.current_stage = "GRAPH_BUILDING"
    db.commit()
    
    # Global entity map for cross-file resolution
    global_entity_map = {}
    for file_result in parsed_results:
        for name, entity_id in file_result["entity_id_map"].items():
            global_entity_map[name] = entity_id
            
    for file_result in parsed_results:
        file_id = file_result["file_id"]
        entity_id_map = file_result["entity_id_map"]
        
        # Add Call Relationships
        for call in file_result["calls"]:
            caller_id = entity_id_map.get(call["caller"])
            if caller_id:
                # Resolve using global map for cross-file support
                target_id = global_entity_map.get(call["callee"])
                if target_id:
                    # Avoid duplicate edges
                    existing = db.query(CallRelationship).filter_by(
                        snapshot_id=uuid.UUID(snapshot_id),
                        caller_id=caller_id,
                        callee_id=target_id
                    ).first()
                    if not existing:
                        db.add(CallRelationship(
                            snapshot_id=uuid.UUID(snapshot_id),
                            caller_id=caller_id,
                            callee_id=target_id,
                            resolution_status="RESOLVED"
                        ))
# Run Cycle Detection
    call_edges = [(str(c.caller_id), str(c.callee_id)) for c in db.query(CallRelationship).filter(CallRelationship.snapshot_id == snapshot_id).all() if c.callee_id]
    
    from apps.analyzer.algorithms import detect_cycles
    from packages.shared.models import AnalysisFinding
    
    cycles = detect_cycles(call_edges)
    for cycle in cycles:
        finding = AnalysisFinding(
            snapshot_id=uuid.UUID(snapshot_id),
            rule_id="ARCH-001",
            severity="WARNING",
            message=f"Circular dependency detected between {len(cycle)} entities.",
            file_id=None,
            line_number=None
        )
        db.add(finding)
        
    db.commit()
    
    # --- PHASE 4: INDEXING (Stub) ---
    job.current_stage = "INDEXING"
    db.commit()
