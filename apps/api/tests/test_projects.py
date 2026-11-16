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
