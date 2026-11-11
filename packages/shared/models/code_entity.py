import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from packages.shared.database import Base

class File(Base):
    __tablename__ = "files"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False)
    path = Column(String, nullable=False, index=True)
    language = Column(String, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    line_count = Column(Integer, nullable=True)
    file_hash = Column(String, nullable=True)
    is_test = Column(Boolean, default=False)
    is_generated = Column(Boolean, default=False)
    is_binary = Column(Boolean, default=False)

    snapshot = relationship("RepositorySnapshot", backref="files")

class CodeEntity(Base):
    __tablename__ = "code_entities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("code_entities.id", ondelete="CASCADE"), nullable=True)
    type = Column(String, nullable=False, index=True) # module, class, function, method
    name = Column(String, nullable=False, index=True)
    start_line = Column(Integer, nullable=True)
    end_line = Column(Integer, nullable=True)
    source_hash = Column(String, nullable=True)

    file = relationship("File", backref="entities")
    parent = relationship("CodeEntity", remote_side=[id], backref="children")

class Module(Base):
    __tablename__ = "modules"
    id = Column(UUID(as_uuid=True), ForeignKey("code_entities.id", ondelete="CASCADE"), primary_key=True)

class ClassEntity(Base):
    __tablename__ = "class_entities"
    id = Column(UUID(as_uuid=True), ForeignKey("code_entities.id", ondelete="CASCADE"), primary_key=True)

class FunctionEntity(Base):
    __tablename__ = "function_entities"
    id = Column(UUID(as_uuid=True), ForeignKey("code_entities.id", ondelete="CASCADE"), primary_key=True)
    is_async = Column(Boolean, default=False)
