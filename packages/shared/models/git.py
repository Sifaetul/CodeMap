import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from packages.shared.database import Base

class GitCommit(Base):
    __tablename__ = "git_commits"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False)
    hash = Column(String, nullable=False, index=True)
    author = Column(String, nullable=True)
    date = Column(DateTime(timezone=True), nullable=True)
    message = Column(String, nullable=True)

class GitFileChange(Base):
    __tablename__ = "git_file_changes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    commit_id = Column(UUID(as_uuid=True), ForeignKey("git_commits.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False) # ADDED, MODIFIED, DELETED
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
