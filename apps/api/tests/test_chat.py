import pytest
import uuid
from packages.shared.models import (
    User, Project, Repository, RepositorySnapshot, File, CodeEntity,
    CallRelationship, ChatSession, ChatMessage
)

def setup_chat_project_and_snapshot(client, db):
    client.post("/api/auth/register", json={"email": "chat@example.com", "password": "password123"})
    res = client.post("/api/auth/login", data={"username": "chat@example.com", "password": "password123"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = client.post("/api/projects", headers=headers, json={"name": "ChatProj"})
    project_id = proj_res.json()["id"]

    repo = Repository(project_id=uuid.UUID(project_id), url="https://github.com/test/chat", source_type="github")
    db.add(repo)
    db.commit()

    snapshot = RepositorySnapshot(repository_id=repo.id)
    db.add(snapshot)
    db.commit()

    file1 = File(snapshot_id=snapshot.id, path="src/service.py", language="python", line_count=25)
    db.add(file1)
    db.commit()

    ent1 = CodeEntity(snapshot_id=snapshot.id, file_id=file1.id, name="OrderService", type="class", start_line=1, end_line=15)
    ent2 = CodeEntity(snapshot_id=snapshot.id, file_id=file1.id, name="validateOrder", type="function", start_line=16, end_line=25)
    db.add_all([ent1, ent2])
    db.commit()

    call = CallRelationship(snapshot_id=snapshot.id, caller_id=ent1.id, callee_id=ent2.id, resolution_status="RESOLVED")
    db.add(call)
    db.commit()

    return {
        "headers": headers,
        "project_id": project_id,
        "snapshot_id": snapshot.id,
        "ent1_id": str(ent1.id),
        "ent2_id": str(ent2.id)
    }

def test_chat_with_architecture_rag_and_persistence(client, db):
    data = setup_chat_project_and_snapshot(client, db)
    headers = data["headers"]
    project_id = data["project_id"]
    ent1_id = data["ent1_id"]

    # 1. Ask question about OrderService
    res = client.post(
        f"/api/projects/{project_id}/chat",
        headers=headers,
        json={"message": "What does OrderService call?", "context_entity_id": ent1_id}
    )
    assert res.status_code == 200
    chat_data = res.json()
    assert "reply" in chat_data
    assert "OrderService" in chat_data["reply"]
    assert "session_id" in chat_data

    # 2. Verify Session & Messages were persisted in Database
    session = db.query(ChatSession).filter(ChatSession.project_id == uuid.UUID(project_id)).first()
    assert session is not None

    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).all()
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[0].content == "What does OrderService call?"
    assert messages[1].role == "assistant"
    assert "OrderService" in messages[1].content

def test_chat_history_retrieval_and_clear(client, db):
    data = setup_chat_project_and_snapshot(client, db)
    headers = data["headers"]
    project_id = data["project_id"]

    # Send a message
    client.post(
        f"/api/projects/{project_id}/chat",
        headers=headers,
        json={"message": "Summarize architecture"}
    )

    # 1. Retrieve history
    history_res = client.get(f"/api/projects/{project_id}/chat/messages", headers=headers)
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) == 2

    # 2. Clear history
    del_res = client.delete(f"/api/projects/{project_id}/chat/messages", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "cleared"

    # Subsequent GET must be empty
    history_after = client.get(f"/api/projects/{project_id}/chat/messages", headers=headers)
    assert len(history_after.json()) == 0

def test_chat_stream_with_architecture(client, db):
    data = setup_chat_project_and_snapshot(client, db)
    headers = data["headers"]
    project_id = data["project_id"]

    res = client.post(
        f"/api/projects/{project_id}/chat/stream",
        headers=headers,
        json={"message": "Stream project summary"}
    )
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    text = res.text
    assert "data: " in text
    assert '"done": true' in text or '"token":' in text
