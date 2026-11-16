import pytest
import uuid
from packages.shared.models import (
    User, Project, Repository, RepositorySnapshot, File, CodeEntity,
    CallRelationship, Dependency
)

def setup_test_project_and_snapshot(client, db):
    # Register & Login
    client.post("/api/auth/register", json={"email": "graph@example.com", "password": "password123"})
    res = client.post("/api/auth/login", data={"username": "graph@example.com", "password": "password123"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create project
    proj_res = client.post("/api/projects", headers=headers, json={"name": "GraphProj"})
    project_id = proj_res.json()["id"]

    user = db.query(User).filter(User.email == "graph@example.com").first()
    
    repo = Repository(project_id=uuid.UUID(project_id), url="https://github.com/test/repo", source_type="github")
    db.add(repo)
    db.commit()

    snapshot = RepositorySnapshot(repository_id=repo.id)
    db.add(snapshot)
    db.commit()

    file1 = File(snapshot_id=snapshot.id, path="src/main.py", language="python", line_count=20)
    file2 = File(snapshot_id=snapshot.id, path="src/utils.py", language="python", line_count=15)
    db.add_all([file1, file2])
    db.commit()

    ent1 = CodeEntity(snapshot_id=snapshot.id, file_id=file1.id, name="main", type="function", start_line=1, end_line=5)
    ent2 = CodeEntity(snapshot_id=snapshot.id, file_id=file2.id, name="helper", type="function", start_line=1, end_line=5)
    db.add_all([ent1, ent2])
    db.commit()

    call = CallRelationship(snapshot_id=snapshot.id, caller_id=ent1.id, callee_id=ent2.id, resolution_status="RESOLVED")
    dep = Dependency(snapshot_id=snapshot.id, source_id=ent1.id, target_id=ent2.id, type="IMPORTS")
    db.add_all([call, dep])
    db.commit()

    return {
        "headers": headers,
        "project_id": project_id,
        "file1_id": str(file1.id),
        "ent1_id": str(ent1.id),
        "ent2_id": str(ent2.id),
    }

def test_get_project_graph(client, db):
    data = setup_test_project_and_snapshot(client, db)
    headers = data["headers"]
    project_id = data["project_id"]

    res = client.get(f"/api/projects/{project_id}/graph", headers=headers)
    assert res.status_code == 200
    graph = res.json()

    assert "nodes" in graph
    assert "edges" in graph
    
    node_types = {n["type"] for n in graph["nodes"]}
    assert "folder" in node_types
    assert "file" in node_types
    assert "custom" in node_types

    edge_types = {e["type"] for e in graph["edges"]}
    assert "containment" in edge_types
    assert "call" in edge_types
    assert "dependency" in edge_types

def test_get_entity_details_with_code_entity(client, db):
    data = setup_test_project_and_snapshot(client, db)
    headers = data["headers"]
    project_id = data["project_id"]
    ent1_id = data["ent1_id"]

    res = client.get(f"/api/projects/{project_id}/entities/{ent1_id}", headers=headers)
    assert res.status_code == 200
    entity_data = res.json()
    assert entity_data["id"] == ent1_id
    assert entity_data["name"] == "main"
    assert entity_data["type"] == "function"
    assert len(entity_data["callees"]) == 1
    assert entity_data["callees"][0]["name"] == "helper"

def test_get_entity_details_with_folder_node(client, db):
    data = setup_test_project_and_snapshot(client, db)
    headers = data["headers"]
    project_id = data["project_id"]

    res = client.get(f"/api/projects/{project_id}/entities/folder-src", headers=headers)
    assert res.status_code == 200
    folder_data = res.json()
    assert folder_data["type"] == "folder"
    assert folder_data["name"] == "src"
    assert "Directory: src" in folder_data["source_code"]

def test_get_entity_details_with_file_node(client, db):
    data = setup_test_project_and_snapshot(client, db)
    headers = data["headers"]
    project_id = data["project_id"]
    file1_id = data["file1_id"]

    res = client.get(f"/api/projects/{project_id}/entities/file-{file1_id}", headers=headers)
    assert res.status_code == 200
    file_data = res.json()
    assert file_data["type"] == "file"
    assert file_data["name"] == "main.py"
    assert len(file_data["callees"]) >= 1
