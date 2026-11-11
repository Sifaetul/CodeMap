from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
