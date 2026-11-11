import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from packages.shared.database import Base

class Project(Base):
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", backref="projects")
    repositories = relationship("Repository", back_populates="project", cascade="all, delete-orphan")

class Repository(Base):
    __tablename__ = "repositories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    source_type = Column(String, nullable=False) # 'github' or 'zip'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="repositories")
    snapshots = relationship("RepositorySnapshot", back_populates="repository", cascade="all, delete-orphan")

class RepositorySnapshot(Base):
    __tablename__ = "repository_snapshots"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    commit_hash = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    repository = relationship("Repository", back_populates="snapshots")
    jobs = relationship("AnalysisJob", back_populates="snapshot", cascade="all, delete-orphan")

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False, default="QUEUED")
    current_stage = Column(String, nullable=True)
    progress = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    snapshot = relationship("RepositorySnapshot", back_populates="jobs")
