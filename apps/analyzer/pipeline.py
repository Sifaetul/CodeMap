from sqlalchemy.orm import Session
from packages.shared.models import (
    AnalysisJob, File, CodeEntity, ClassEntity, FunctionEntity, Module,
    Dependency, CallRelationship, AnalysisFinding
)
from apps.analyzer.scanner import RepositoryScanner
from apps.analyzer.parsers import get_parser_for_path, detect_language
from apps.analyzer.algorithms import (
    detect_cycles, compute_pagerank, compute_coupling_metrics,
    detect_dead_code, detect_god_components
)
import os
import uuid
from collections import defaultdict

def run_analysis_pipeline(db: Session, snapshot_id: str, workspace_dir: str, job: AnalysisJob):
    parsed_snapshot_uuid = uuid.UUID(snapshot_id)

    # --- PHASE 1: SCANNING ---
    job.current_stage = "SCANNING"
    job.progress = "15%"
    db.commit()
    
    scanner = RepositoryScanner(workspace_dir)
    files_by_ext = scanner.scan()
    
    file_records = {}
    for ext, rel_paths in files_by_ext.items():
        for rel_path in rel_paths:
            f = File(
                snapshot_id=parsed_snapshot_uuid,
                path=rel_path,
                language=detect_language(rel_path)
            )
            db.add(f)
            file_records[rel_path] = f
            
    db.commit()

    # --- PHASE 2: PARSING (Polyglot: Python & JavaScript/TypeScript) ---
    job.current_stage = "PARSING"
    job.progress = "40%"
    db.commit()
    
    # Collect all parseable files
    parseable_files = [
        path for path in file_records.keys()
        if get_parser_for_path(path) is not None
    ]
    
    parsed_results = []
    module_records = {}  # rel_path / module_name -> module CodeEntity.id
    all_entity_ids = []
    entrypoint_ids = set()
    
    for rel_path in parseable_files:
        abs_path = os.path.join(workspace_dir, rel_path)
        file_record = file_records[rel_path]
        parser = get_parser_for_path(rel_path)
        if not parser:
            continue
        
        # Create a top-level Module CodeEntity representing the file
        module_name = os.path.splitext(rel_path)[0].replace("/", ".")
        module_ce = CodeEntity(
            snapshot_id=parsed_snapshot_uuid,
            file_id=file_record.id,
            name=module_name,
            type="module",
            start_line=1,
            end_line=file_record.line_count or 1
        )
        db.add(module_ce)
        db.flush()
        db.add(Module(id=module_ce.id))
        module_records[rel_path] = module_ce.id
        module_records[module_name] = module_ce.id
        all_entity_ids.append(str(module_ce.id))

        # Check if entrypoint file (main, index, app)
        base_filename = os.path.basename(rel_path).lower()
        if any(base_filename.startswith(p) for p in ["main.", "index.", "app.", "server."]):
            entrypoint_ids.add(str(module_ce.id))

        try:
            with open(abs_path, 'r', encoding='utf-8') as f_in:
                content = f_in.read()
                
            result = parser.parse(content, rel_path)
            
            # Map entity names to their DB IDs for this file
            entity_id_map = {}
            
            for ent in result["entities"]:
                ce = CodeEntity(
                    snapshot_id=parsed_snapshot_uuid,
                    file_id=file_record.id,
                    parent_id=module_ce.id,
                    name=ent["name"],
                    type=ent["type"],
                    start_line=ent["start_line"],
                    end_line=ent["end_line"],
                )
                db.add(ce)
                db.flush()
                entity_id_map[ent["name"]] = ce.id
                all_entity_ids.append(str(ce.id))
                
                if ent["name"] in ["main", "handler", "default", "App"]:
                    entrypoint_ids.add(str(ce.id))

                if ent["type"] == "class":
                    db.add(ClassEntity(id=ce.id))
                elif ent["type"] == "function":
                    db.add(FunctionEntity(id=ce.id, is_async=False))
            
            parsed_results.append({
                "file_id": file_record.id,
                "rel_path": rel_path,
                "module_name": module_name,
                "module_id": module_ce.id,
                "entity_id_map": entity_id_map,
                "imports": result["imports"],
                "calls": result["calls"]
            })
                    
        except Exception as e:
            print(f"Pipeline error processing {rel_path}: {e}")
            
    db.commit()

    # --- PHASE 3: GRAPH BUILDING ---
    job.current_stage = "GRAPH_BUILDING"
    job.progress = "70%"
    db.commit()
    
    # 1. Build Entity Lookup indexes to prevent cross-file collision
    entities_by_name = defaultdict(list)
    for file_result in parsed_results:
        for name, entity_id in file_result["entity_id_map"].items():
            entities_by_name[name].append((file_result["rel_path"], entity_id))
            
    # 2. Persist Module Dependencies from Imports
    for file_result in parsed_results:
        src_module_id = file_result["module_id"]
        
        for imp in file_result["imports"]:
            imp_name = imp.get("name", "")
            # Check if imported name maps to any known module in project
            matched_target_id = None
            
            if imp_name in module_records:
                matched_target_id = module_records[imp_name]
            else:
                parts = imp_name.split(".")
                for i in range(len(parts), 0, -1):
                    prefix = ".".join(parts[:i])
                    if prefix in module_records:
                        matched_target_id = module_records[prefix]
                        break

            if matched_target_id and matched_target_id != src_module_id:
                existing_dep = db.query(Dependency).filter_by(
                    snapshot_id=parsed_snapshot_uuid,
                    source_id=src_module_id,
                    target_id=matched_target_id,
                    type="IMPORTS"
                ).first()
                if not existing_dep:
                    db.add(Dependency(
                        snapshot_id=parsed_snapshot_uuid,
                        source_id=src_module_id,
                        target_id=matched_target_id,
                        type="IMPORTS",
                        line_number=imp.get("line")
                    ))

    # 3. Add Call Relationships with collision-free resolution
    for file_result in parsed_results:
        local_entity_map = file_result["entity_id_map"]
        imported_names = {imp["name"].split(".")[-1]: imp["name"] for imp in file_result["imports"]}
        
        for call in file_result["calls"]:
            caller_id = local_entity_map.get(call["caller"])
            if not caller_id:
                continue

            callee_name = call["callee"]
            target_id = None
            
            # Step A: Local scope resolution
            if callee_name in local_entity_map:
                target_id = local_entity_map[callee_name]
            
            # Step B: Explicit Import Resolution
            elif callee_name in imported_names:
                full_import_name = imported_names[callee_name]
                candidates = entities_by_name.get(callee_name, [])
                for candidate_path, cand_id in candidates:
                    cand_mod = os.path.splitext(candidate_path)[0].replace("/", ".")
                    if full_import_name.startswith(cand_mod) or cand_mod.endswith(full_import_name.rsplit(".", 1)[0]):
                        target_id = cand_id
                        break
            
            # Step C: Unique Global Match
            elif len(entities_by_name.get(callee_name, [])) == 1:
                target_id = entities_by_name[callee_name][0][1]

            if target_id:
                existing = db.query(CallRelationship).filter_by(
                    snapshot_id=parsed_snapshot_uuid,
                    caller_id=caller_id,
                    callee_id=target_id
                ).first()
                if not existing:
                    db.add(CallRelationship(
                        snapshot_id=parsed_snapshot_uuid,
                        caller_id=caller_id,
                        callee_id=target_id,
                        resolution_status="RESOLVED",
                        line_number=call.get("line")
                    ))
            else:
                db.add(CallRelationship(
                    snapshot_id=parsed_snapshot_uuid,
                    caller_id=caller_id,
                    callee_id=None,
                    callee_name=callee_name,
                    resolution_status="UNRESOLVED",
                    line_number=call.get("line")
                ))

    # 4. Deep Graph Algorithms & Architecture Smells
    call_edges = [
        (str(c.caller_id), str(c.callee_id))
        for c in db.query(CallRelationship).filter(
            CallRelationship.snapshot_id == parsed_snapshot_uuid,
            CallRelationship.callee_id.isnot(None)
        ).all()
    ]
    
    # A. Circular Dependency Detection (Tarjan SCC)
    cycles = detect_cycles(call_edges)
    for cycle in cycles:
        db.add(AnalysisFinding(
            snapshot_id=parsed_snapshot_uuid,
            type="CIRCULAR_DEPENDENCY",
            severity="WARNING",
            description=f"Circular dependency detected between {len(cycle)} entities in call graph.",
            confidence=1.0
        ))

    # B. Dead Code / Orphan Analysis
    dead_nodes = detect_dead_code(all_entity_ids, call_edges, entrypoints=entrypoint_ids)
    for dead_id in dead_nodes[:20]: # Cap top 20 to avoid overwhelming findings
        dead_uuid = uuid.UUID(dead_id)
        ent = db.query(CodeEntity).filter_by(id=dead_uuid).first()
        if ent and ent.type in ["function", "class"]:
            db.add(AnalysisFinding(
                snapshot_id=parsed_snapshot_uuid,
                type="DEAD_CODE",
                severity="INFO",
                description=f"Entity '{ent.name}' ({ent.type}) has no incoming calls in codebase.",
                confidence=0.85
            ))

    # C. God Component Detection
    god_components = detect_god_components(all_entity_ids, call_edges, threshold=6)
    for god in god_components:
        god_uuid = uuid.UUID(god["node_id"])
        ent = db.query(CodeEntity).filter_by(id=god_uuid).first()
        if ent:
            db.add(AnalysisFinding(
                snapshot_id=parsed_snapshot_uuid,
                type="GOD_COMPONENT",
                severity="WARNING",
                description=f"Entity '{ent.name}' ({ent.type}) is overly coupled with {god['total_connections']} connections (Instability: {god['instability']}).",
                confidence=0.9
            ))
        
    db.commit()
    
    # --- PHASE 4: INDEXING & COMPLETION ---
    job.current_stage = "COMPLETED"
    job.progress = "100%"
    job.status = "COMPLETED"
    db.commit()
