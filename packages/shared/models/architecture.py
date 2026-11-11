import uuid
from sqlalchemy import Column, String, ForeignKey, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from packages.shared.database import Base, JSONType

class ArchitectureComponent(Base):
    __tablename__ = "architecture_components"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    confidence = Column(Float, default=1.0)
    evidence = Column(JSONType, nullable=True)

class ArchitectureRelationship(Base):
    __tablename__ = "architecture_relationships"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False)
    source_component_id = Column(UUID(as_uuid=True), ForeignKey("architecture_components.id", ondelete="CASCADE"), nullable=False)
    target_component_id = Column(UUID(as_uuid=True), ForeignKey("architecture_components.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False)
