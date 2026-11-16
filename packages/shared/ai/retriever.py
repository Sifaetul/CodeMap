from typing import Dict, Any, List, Optional
import os
import uuid
from sqlalchemy.orm import Session
from packages.shared.models import (
    CodeEntity, File, CallRelationship, Dependency, AnalysisFinding, RepositorySnapshot
)
from packages.shared.utils.workspace import get_workspace_dir

def retrieve_architecture_context(
    db: Session,
    snapshot_id: uuid.UUID,
    query: str,
    context_entity_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves rich architectural context from the database graph and AST
    for prompt injection into the AI LLM.
    """
    context: Dict[str, Any] = {
        "focused_entity": None,
        "related_entities": [],
        "call_relationships": [],
        "dependencies": [],
        "findings": [],
        "stats": {}
    }

    # 1. Total statistics
    total_files = db.query(File).filter(File.snapshot_id == snapshot_id).count()
    total_entities = db.query(CodeEntity).filter(CodeEntity.snapshot_id == snapshot_id).count()
    total_calls = db.query(CallRelationship).filter(CallRelationship.snapshot_id == snapshot_id).count()
    total_deps = db.query(Dependency).filter(Dependency.snapshot_id == snapshot_id).count()
    
    context["stats"] = {
        "files_count": total_files,
        "entities_count": total_entities,
        "calls_count": total_calls,
        "dependencies_count": total_deps
    }

    # 2. Focused Entity Details (if user selected a node in the graph)
    if context_entity_id:
        # Check if folder or file node
        if context_entity_id.startswith("folder-"):
            folder_path = context_entity_id[len("folder-"):]
            context["focused_entity"] = {
                "name": folder_path.split("/")[-1],
                "type": "directory",
                "path": folder_path,
                "source_snippet": f"Directory: {folder_path}"
            }
        elif context_entity_id.startswith("file-"):
            file_uuid_str = context_entity_id[len("file-"):]
            try:
                f_obj = db.query(File).filter(File.id == uuid.UUID(file_uuid_str)).first()
                if f_obj:
                    context["focused_entity"] = {
                        "name": f_obj.path.split("/")[-1],
                        "type": "file",
                        "path": f_obj.path,
                        "language": f_obj.language
                    }
            except Exception:
                pass
        else:
            try:
                ent_uuid = uuid.UUID(context_entity_id)
                ent = db.query(CodeEntity).filter(CodeEntity.id == ent_uuid).first()
                if ent:
                    # Get file and source code
                    file_obj = db.query(File).filter(File.id == ent.file_id).first()
                    snippet = ""
                    if file_obj:
                        ws_dir = get_workspace_dir(str(snapshot_id))
                        fp = os.path.join(ws_dir, file_obj.path)
                        if os.path.exists(fp):
                            try:
                                with open(fp, "r", encoding="utf-8") as f_in:
                                    lines = f_in.readlines()
                                    if ent.start_line and ent.end_line:
                                        snippet = "".join(lines[ent.start_line - 1 : ent.end_line])
                            except Exception:
                                pass

                    # Callers and Callees
                    callers = db.query(CallRelationship).filter(CallRelationship.callee_id == ent.id).all()
                    callees = db.query(CallRelationship).filter(CallRelationship.caller_id == ent.id).all()

                    caller_names = [c.caller.name for c in callers if c.caller]
                    callee_names = [c.callee.name for c in callees if c.callee]

                    context["focused_entity"] = {
                        "name": ent.name,
                        "type": ent.type,
                        "file_path": file_obj.path if file_obj else "",
                        "start_line": ent.start_line,
                        "end_line": ent.end_line,
                        "source_snippet": snippet[:1500],
                        "callers": caller_names[:10],
                        "callees": callee_names[:10]
                    }
            except Exception:
                pass

    # 3. Retrieve relevant entities using targeted SQL search
    from sqlalchemy import or_
    tokens = [t.lower() for t in query.replace("?", " ").replace(",", " ").split() if len(t) > 2]
    context["related_entities"] = []

    if tokens:
        search_clauses = [CodeEntity.name.ilike(f"%{tok}%") for tok in tokens[:8]]
        matched_entities = (
            db.query(CodeEntity)
            .filter(CodeEntity.snapshot_id == snapshot_id, or_(*search_clauses))
            .limit(10)
            .all()
        )
        context["related_entities"] = [
            {"id": str(e.id), "name": e.name, "type": e.type}
            for e in matched_entities[:6]
        ]

    # 4. Relevant architectural findings
    findings = db.query(AnalysisFinding).filter(AnalysisFinding.snapshot_id == snapshot_id).all()
    context["findings"] = [
        {"type": f.type, "severity": f.severity, "description": f.description}
        for f in findings[:5]
    ]

    return context

def build_rag_prompt(query: str, context: Dict[str, Any]) -> str:
    """Builds a comprehensive LLM prompt with retrieved architecture context."""
    prompt_parts = [
        "You are CodeAtlas Architecture Intelligence, an expert senior software architect.",
        "Your task is to analyze and answer questions about the software architecture accurately using the retrieved codebase facts below.\n",
        "=== Architecture Context ===",
        f"- Repository Size: {context['stats'].get('files_count', 0)} files, {context['stats'].get('entities_count', 0)} code entities.",
        f"- Interactions: {context['stats'].get('calls_count', 0)} calls, {context['stats'].get('dependencies_count', 0)} module dependencies."
    ]

    # Focused entity
    if context.get("focused_entity"):
        fe = context["focused_entity"]
        prompt_parts.append("\n=== Currently Focused Component ===")
        prompt_parts.append(f"- Name: {fe.get('name')} ({fe.get('type')})")
        if fe.get("file_path"):
            prompt_parts.append(f"- File Path: {fe.get('file_path')} (Lines {fe.get('start_line')}-{fe.get('end_line')})")
        if fe.get("callers"):
            prompt_parts.append(f"- Called By: {', '.join(fe['callers'])}")
        if fe.get("callees"):
            prompt_parts.append(f"- Calls: {', '.join(fe['callees'])}")
        if fe.get("source_snippet"):
            prompt_parts.append(f"```\n{fe['source_snippet']}\n```")

    # Related entities
    if context.get("related_entities"):
        prompt_parts.append("\n=== Relevant Components Identified ===")
        for re in context["related_entities"]:
            prompt_parts.append(f"- {re['type']}: {re['name']}")

    # Architectural findings
    if context.get("findings"):
        prompt_parts.append("\n=== Known Architectural Findings / Smells ===")
        for f in context["findings"]:
            prompt_parts.append(f"- [{f['severity']}] {f['type']}: {f['description']}")

    prompt_parts.append("\n=== User Question ===")
    prompt_parts.append(query)
    prompt_parts.append("\n=== Instructions ===")
    prompt_parts.append("Provide a clear, precise, and senior-developer level explanation. Detail responsibilities, dependencies, and potential ripple effects when modifying this code.")

    return "\n".join(prompt_parts)

def synthesize_architecture_fallback(query: str, context: Dict[str, Any]) -> str:
    """
    Intelligent fallback response synthesizer when local Ollama daemon is offline.
    Directly answers using real AST, graph edges, and findings.
    """
    fe = context.get("focused_entity")
    findings = context.get("findings", [])
    related = context.get("related_entities", [])
    stats = context.get("stats", {})

    msg = query.lower()

    if fe:
        name = fe.get("name", "Component")
        ent_type = fe.get("type", "entity")
        callers = fe.get("callers", [])
        callees = fe.get("callees", [])
        path = fe.get("file_path", "")

        reply = f"### Component Analysis: `{name}` ({ent_type})\n\n"
        if path:
            reply += f"Located in `{path}`"
            if fe.get("start_line") and fe.get("end_line"):
                reply += f" (Lines {fe['start_line']}–{fe['end_line']})"
            reply += ".\n\n"

        if "dependency" in msg or "call" in msg or "ripple" in msg or "effect" in msg:
            reply += "**Dependency & Coupling Impact:**\n"
            if callers:
                reply += f"- **Inbound Callers ({len(callers)}):** Depended on by `{', '.join(callers)}`. Modifying `{name}` requires verifying these dependents.\n"
            else:
                reply += "- **Inbound Callers:** None detected (acts as an entrypoint or standalone entity).\n"

            if callees:
                reply += f"- **Outbound Calls ({len(callees)}):** Calls into `{', '.join(callees)}`.\n"
            else:
                reply += "- **Outbound Calls:** None detected.\n"
        else:
            reply += f"`{name}` serves as a key {ent_type} in this module. "
            if callees:
                reply += f"It coordinates operations across `{', '.join(callees[:4])}`. "
            if callers:
                reply += f"It is invoked by `{', '.join(callers[:4])}`. "
            reply += "\n\nFeel free to ask about its dependencies, callers, or refactoring suggestions."
        return reply

    if "finding" in msg or "issue" in msg or "cycle" in msg or "smell" in msg or "dead" in msg:
        if findings:
            reply = "### Architectural Findings Detected\n\n"
            for f in findings:
                reply += f"- **[{f['severity']}] {f['type']}**: {f['description']}\n"
            return reply
        else:
            return "No critical architecture smells or circular dependencies were flagged in this snapshot."

    # General architecture summary
    reply = f"### Codebase Architecture Overview\n\n"
    reply += f"This codebase comprises **{stats.get('files_count', 0)} files** and **{stats.get('entities_count', 0)} analyzed code entities**, connected by **{stats.get('calls_count', 0)} function call relationships** and **{stats.get('dependencies_count', 0)} module imports**.\n\n"
    
    if related:
        reply += "**Key Components Matching Your Query:**\n"
        for r in related:
            reply += f"- `{r['name']}` ({r['type']})\n"
        reply += "\nClick on any node in the interactive architecture graph to inspect its source code, callers, and callees in depth."
    else:
        reply += "You can click on any node in the graph and ask me about its role, inbound callers, outbound dependencies, or architectural stability score."
    
    return reply
