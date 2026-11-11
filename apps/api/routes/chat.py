from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
import os

from packages.shared.models import Project, CodeEntity, CallRelationship
from apps.api.core.deps import get_db, get_current_user

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    context_entity_id: str | None = None

@router.post("/{project_id}/chat")
def chat_with_architecture(
    project_id: UUID,
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Here we would normally use LangChain or google-generativeai.
    # Since we are creating a robust mock for the UI preview:
    
    msg = request.message.lower()
    
    if request.context_entity_id:
        ent = db.query(CodeEntity).filter(CodeEntity.id == request.context_entity_id).first()
        if ent:
            reply = f"I see you are looking at `{ent.name}` (a {ent.type}). "
            if "what" in msg or "explain" in msg or "how" in msg:
                reply += f"Based on my analysis, `{ent.name}` is responsible for core logic in this domain. It takes inputs and processes them."
            elif "dependency" in msg or "call" in msg or "effect" in msg:
                reply += f"If you modify `{ent.name}`, you must check its dependents carefully, as it's tightly coupled to the modules connecting to it."
            else:
                reply += "How else can I help you understand this specific entity?"
            return {"reply": reply}
            
    # Generic responses
    if "structure" in msg or "architecture" in msg:
        return {"reply": "This project follows a modular architecture. I detected multiple interconnected components. The main entry points seem to be at the top of the tree, orchestrating data flow downwards."}
    if "summary" in msg or "overview" in msg:
        entities = db.query(CodeEntity).filter(CodeEntity.snapshot_id == project.snapshots[-1].id).count() if project.snapshots else 0
        return {"reply": f"This project contains {entities} analyzed code entities. It is well-structured but could use some decoupling in the central modules."}
        
    return {"reply": "I am analyzing your architecture... I can explain specific functions, summarize the project structure, or trace dependencies. Try clicking on a node and asking me about it!"}
