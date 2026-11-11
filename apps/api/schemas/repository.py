from pydantic import BaseModel, HttpUrl
from uuid import UUID
from datetime import datetime

class GithubImportRequest(BaseModel):
    url: str

class RepositorySnapshotResponse(BaseModel):
    id: UUID
    repository_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class RepositoryResponse(BaseModel):
    id: UUID
    project_id: UUID
    url: str
    source_type: str
    created_at: datetime
    snapshots: list[RepositorySnapshotResponse] = []

    class Config:
        from_attributes = True
