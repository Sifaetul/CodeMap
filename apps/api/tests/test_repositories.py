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

def test_is_safe_path_security_checks():
    from packages.shared.utils.zip import is_safe_path
    base = "/tmp/codeatlas_workspaces/snap-123"
    
    # Valid subpaths
    assert is_safe_path("/tmp/codeatlas_workspaces/snap-123/src/index.js", base) is True
    assert is_safe_path("/tmp/codeatlas_workspaces/snap-123/file.txt", base) is True

    # Path traversal with parent directory
    assert is_safe_path("/tmp/codeatlas_workspaces/snap-123/../../etc/passwd", base) is False
    assert is_safe_path("/tmp/codeatlas_workspaces/snap-123/../snap-124/evil.py", base) is False

    # Prefix confusion attack (snap-123_evil starting with snap-123)
    assert is_safe_path("/tmp/codeatlas_workspaces/snap-123_evil/file.py", base) is False
