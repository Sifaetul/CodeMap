import pytest
import uuid
from packages.shared.models import (
    User, Project, Repository, RepositorySnapshot, AnalysisFinding
)

def test_get_project_findings(client, db):
    # Register & Login
    client.post("/api/auth/register", json={"email": "findings@example.com", "password": "password123"})
    res = client.post("/api/auth/login", data={"username": "findings@example.com", "password": "password123"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create project
    proj_res = client.post("/api/projects", headers=headers, json={"name": "FindingsProj"})
    project_id = proj_res.json()["id"]

    repo = Repository(project_id=uuid.UUID(project_id), url="https://github.com/test/findings", source_type="github")
    db.add(repo)
    db.commit()

    snapshot = RepositorySnapshot(repository_id=repo.id)
    db.add(snapshot)
    db.commit()

    finding1 = AnalysisFinding(
        snapshot_id=snapshot.id,
        type="DEAD_CODE",
        severity="INFO",
        description="Dead code detected in old_util.py",
        confidence=0.9
    )
    finding2 = AnalysisFinding(
        snapshot_id=snapshot.id,
        type="CIRCULAR_DEPENDENCY",
        severity="WARNING",
        description="Circular loop between A and B",
        confidence=1.0
    )
    db.add_all([finding1, finding2])
    db.commit()

    res = client.get(f"/api/analysis/projects/{project_id}/findings", headers=headers)
    assert res.status_code == 200
    findings = res.json()
    assert len(findings) == 2
    types = {f["type"] for f in findings}
    assert "DEAD_CODE" in types
    assert "CIRCULAR_DEPENDENCY" in types
