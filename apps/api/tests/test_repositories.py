import pytest

def get_auth_token(client):
    client.post("/api/auth/register", json={"email": "test@example.com", "password": "password123"})
    res = client.post("/api/auth/login", data={"username": "test@example.com", "password": "password123"})
    return res.json()["access_token"]

def test_github_import_invalid_url(client):
    token = get_auth_token(client)
    project_res = client.post("/api/projects", headers={"Authorization": f"Bearer {token}"}, json={"name": "P1"})
    project_id = project_res.json()["id"]

    res = client.post(
        f"/api/projects/{project_id}/repositories/github",
        headers={"Authorization": f"Bearer {token}"},
        json={"url": "https://malicious.com/repo"}
    )
    assert res.status_code == 400
    assert "Invalid GitHub URL" in res.json()["detail"]
