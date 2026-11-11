import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.main import app
from packages.shared.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_projects.db"
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

def get_auth_token_user2():
    client.post("/api/auth/register", json={"email": "user2@example.com", "password": "password123"})
    res = client.post("/api/auth/login", data={"username": "user2@example.com", "password": "password123"})
    return res.json()["access_token"]

def test_create_project():
    token = get_auth_token()
    response = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "My Project", "description": "Test Project"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "My Project"

def test_isolation():
    token1 = get_auth_token()
    token2 = get_auth_token_user2()
    
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
