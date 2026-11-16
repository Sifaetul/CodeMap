from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import asyncio

from packages.shared.models import (
    Project, User, Repository, RepositorySnapshot, ChatSession, ChatMessage
)
from apps.api.core.deps import get_db, get_current_user
from packages.shared.ai.provider import OllamaProvider
from packages.shared.ai.retriever import (
    retrieve_architecture_context, build_rag_prompt, synthesize_architecture_fallback
)

router = APIRouter()
ollama_provider = OllamaProvider()

class ChatRequest(BaseModel):
    message: str
    context_entity_id: Optional[str] = None

def _get_or_create_session(db: Session, project: Project, user: User, snapshot_id: UUID) -> ChatSession:
    session = db.query(ChatSession).filter(
        ChatSession.project_id == project.id,
        ChatSession.user_id == user.id,
        ChatSession.snapshot_id == snapshot_id
    ).first()
    if not session:
        session = ChatSession(
            project_id=project.id,
            user_id=user.id,
            snapshot_id=snapshot_id
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    return session

@router.post("/{project_id}/chat")
async def chat_with_architecture(
    project_id: UUID,
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    snapshot = db.query(RepositorySnapshot).join(Repository).filter(Repository.project_id == project.id).order_by(RepositorySnapshot.created_at.desc()).first()
    if not snapshot:
        return {"reply": "No repository snapshot found for this project. Please import a repository first."}

    # 1. Retrieve Architecture Context
    context = retrieve_architecture_context(
        db=db,
        snapshot_id=snapshot.id,
        query=request.message,
        context_entity_id=request.context_entity_id
    )

    # 2. Build RAG Prompt
    prompt = build_rag_prompt(request.message, context)

    # 3. Generate response via Ollama or Intelligent Fallback
    reply = ""
    is_ollama_online = await ollama_provider.is_available()
    if is_ollama_online:
        raw_reply = await ollama_provider.generate(prompt)
        if not raw_reply.startswith("AI Error:"):
            reply = raw_reply

    if not reply:
        reply = synthesize_architecture_fallback(request.message, context)

    # 4. Persist in ChatSession and ChatMessage
    session = _get_or_create_session(db, project, current_user, snapshot.id)
    
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=request.message,
        evidence={"context_entity_id": request.context_entity_id}
    )
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=reply,
        evidence={"stats": context.get("stats"), "focused": context.get("focused_entity", {}).get("name") if context.get("focused_entity") else None}
    )
    db.add_all([user_msg, assistant_msg])
    db.commit()

    return {
        "reply": reply,
        "session_id": str(session.id),
        "context": {
            "focused_entity": context.get("focused_entity", {}).get("name") if context.get("focused_entity") else None,
            "relevant_count": len(context.get("related_entities", []))
        }
    }

@router.post("/{project_id}/chat/stream")
async def chat_stream_with_architecture(
    project_id: UUID,
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    snapshot = db.query(RepositorySnapshot).join(Repository).filter(Repository.project_id == project.id).order_by(RepositorySnapshot.created_at.desc()).first()
    if not snapshot:
        raise HTTPException(status_code=400, detail="No snapshot found for this project")

    context = retrieve_architecture_context(
        db=db,
        snapshot_id=snapshot.id,
        query=request.message,
        context_entity_id=request.context_entity_id
    )
    prompt = build_rag_prompt(request.message, context)
    session = _get_or_create_session(db, project, current_user, snapshot.id)
    session_uuid = session.id

    # Save user message
    user_msg = ChatMessage(
        session_id=session_uuid,
        role="user",
        content=request.message,
        evidence={"context_entity_id": request.context_entity_id}
    )
    db.add(user_msg)
    db.commit()

    async def event_generator():
        collected_tokens = []
        is_ollama_online = await ollama_provider.is_available()

        if is_ollama_online:
            async for token in ollama_provider.stream_generate(prompt):
                collected_tokens.append(token)
                yield f"data: {json.dumps({'token': token})}\n\n"
        else:
            # Fallback simulated stream of tokens
            fallback_text = synthesize_architecture_fallback(request.message, context)
            words = fallback_text.split(" ")
            for i, word in enumerate(words):
                token = word if i == 0 else " " + word
                collected_tokens.append(token)
                yield f"data: {json.dumps({'token': token})}\n\n"
                await asyncio.sleep(0.01)

        full_reply = "".join(collected_tokens)
        yield f"data: {json.dumps({'done': True, 'full_reply': full_reply})}\n\n"

        # Save assistant message using a fresh session on the same engine
        from sqlalchemy.orm import sessionmaker
        StreamSession = sessionmaker(bind=db.bind)
        db_stream = StreamSession()
        try:
            assistant_msg = ChatMessage(
                session_id=session_uuid,
                role="assistant",
                content=full_reply,
                evidence={"streamed": True}
            )
            db_stream.add(assistant_msg)
            db_stream.commit()
        finally:
            db_stream.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/{project_id}/chat/messages")
def get_chat_history(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    session = db.query(ChatSession).filter(
        ChatSession.project_id == project.id,
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.created_at.desc()).first()

    if not session:
        return []

    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at.asc()).all()
    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "evidence": m.evidence,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in messages
    ]

@router.delete("/{project_id}/chat/messages")
def clear_chat_history(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    sessions = db.query(ChatSession).filter(
        ChatSession.project_id == project.id,
        ChatSession.user_id == current_user.id
    ).all()

    for s in sessions:
        db.query(ChatMessage).filter(ChatMessage.session_id == s.id).delete()
        db.delete(s)
    db.commit()

    return {"status": "cleared"}
