import pytest

def get_auth_token(client):
    client.post("/api/auth/register", json={"email": "test@example.com", "password": "password123"})
    res = client.post("/api/auth/login", data={"username": "test@example.com", "password": "password123"})
    return res.json()["access_token"]

def get_auth_token_user2(client):
    client.post("/api/auth/register", json={"email": "user2@example.com", "password": "password123"})
    res = client.post("/api/auth/login", data={"username": "user2@example.com", "password": "password123"})
    return res.json()["access_token"]

def test_create_project(client):
    token = get_auth_token(client)
    response = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "My Project", "description": "Test Project"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "My Project"

def test_isolation(client):
    token1 = get_auth_token(client)
    token2 = get_auth_token_user2(client)
    
    # User 1 creates project
    res = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token1}"},
        json={"name": "User 1 Project"}
    )
    project_id = res.json()["id"]

    # User 2 tries to get User 1's project
    res_get = client.get(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert res_get.status_code == 404

def test_delete_project_cleans_workspace(client, db):
    import os
    from uuid import uuid4
    from packages.shared.models import Repository, RepositorySnapshot
    from packages.shared.utils.workspace import get_workspace_dir

    token = get_auth_token(client)
    res = client.post("/api/projects", headers={"Authorization": f"Bearer {token}"}, json={"name": "To Delete"})
    project_id = res.json()["id"]

    # Seed repository and snapshot with proper UUID objects
    from uuid import UUID as PyUUID
    repo = Repository(project_id=PyUUID(project_id), url="test.zip", source_type="zip")
    db.add(repo)
    db.commit()

    snap = RepositorySnapshot(repository_id=repo.id)
    db.add(snap)
    db.commit()

    ws_dir = get_workspace_dir(str(snap.id))
    dummy_file = os.path.join(ws_dir, "test.txt")
    with open(dummy_file, "w") as f:
        f.write("hello")
    assert os.path.exists(dummy_file)

    # Delete project via API
    del_res = client.delete(f"/api/projects/{project_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 204

    # Verify workspace directory is wiped from disk
    assert not os.path.exists(ws_dir)
