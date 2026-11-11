import uuid
from sqlalchemy import Column, String, ForeignKey, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from packages.shared.database import Base

class Dependency(Base):
    __tablename__ = "dependencies"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(UUID(as_uuid=True), ForeignKey("code_entities.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(UUID(as_uuid=True), ForeignKey("code_entities.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False) # IMPORTS, USES, EXTENDS
    confidence = Column(Float, default=1.0)
    line_number = Column(Integer, nullable=True)

    source = relationship("CodeEntity", foreign_keys=[source_id])
    target = relationship("CodeEntity", foreign_keys=[target_id])

class CallRelationship(Base):
    __tablename__ = "call_relationships"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False)
    caller_id = Column(UUID(as_uuid=True), ForeignKey("code_entities.id", ondelete="CASCADE"), nullable=False)
    callee_id = Column(UUID(as_uuid=True), ForeignKey("code_entities.id", ondelete="CASCADE"), nullable=True) # True if unresolved
    callee_name = Column(String, nullable=True)
    resolution_status = Column(String, nullable=False) # RESOLVED, UNRESOLVED
    line_number = Column(Integer, nullable=True)

    caller = relationship("CodeEntity", foreign_keys=[caller_id])
    callee = relationship("CodeEntity", foreign_keys=[callee_id])
