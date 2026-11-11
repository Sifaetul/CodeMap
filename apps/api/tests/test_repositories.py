import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.main import app
from packages.shared.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_repos.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def get_auth_token():
    client.post("/api/auth/register", json={"email": "test@example.com", "password": "password123"})
    res = client.post("/api/auth/login", data={"username": "test@example.com", "password": "password123"})
    return res.json()["access_token"]

def test_github_import_invalid_url():
    token = get_auth_token()
    project_res = client.post("/api/projects", headers={"Authorization": f"Bearer {token}"}, json={"name": "P1"})
    project_id = project_res.json()["id"]

    res = client.post(
        f"/api/projects/{project_id}/repositories/github",
        headers={"Authorization": f"Bearer {token}"},
        json={"url": "https://malicious.com/repo"}
    )
    assert res.status_code == 400
    assert "Invalid GitHub URL" in res.json()["detail"]
