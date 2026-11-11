import uuid
from sqlalchemy import Column, String, ForeignKey, Float, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from packages.shared.database import Base

class ApiEndpoint(Base):
    __tablename__ = "api_endpoints"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("code_entities.id", ondelete="CASCADE"), nullable=False)
    method = Column(String, nullable=False)
    route = Column(String, nullable=False)
    framework = Column(String, nullable=True)
    confidence = Column(Float, default=1.0)

class DatabaseEntity(Base):
    __tablename__ = "database_entities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("code_entities.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False) # Model, Repository, Query

class DatabaseReference(Base):
    __tablename__ = "database_references"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("code_entities.id", ondelete="CASCADE"), nullable=False)
    operation = Column(String, nullable=False) # READ, WRITE

class TestEntity(Base):
    __tablename__ = "test_entities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("code_entities.id", ondelete="CASCADE"), nullable=False)

class TestReference(Base):
    __tablename__ = "test_references"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False)
    test_id = Column(UUID(as_uuid=True), ForeignKey("test_entities.id", ondelete="CASCADE"), nullable=False)
    target_entity_id = Column(UUID(as_uuid=True), ForeignKey("code_entities.id", ondelete="CASCADE"), nullable=False)

class AnalysisFinding(Base):
    __tablename__ = "analysis_findings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    evidence = Column(JSONB, nullable=True)
    confidence = Column(Float, default=1.0)
