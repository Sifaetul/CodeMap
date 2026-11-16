import pytest
import tempfile
import os
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from packages.shared.database import Base
from packages.shared.models import (
    AnalysisJob, File, CodeEntity, Dependency, CallRelationship, AnalysisFinding
)
from apps.analyzer.pipeline import run_analysis_pipeline

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_pipeline.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_pipeline_collision_free_and_dependency_persistence():
    with tempfile.TemporaryDirectory() as temp_dir:
        os.makedirs(os.path.join(temp_dir, "utils"), exist_ok=True)
        with open(os.path.join(temp_dir, "utils", "common.py"), "w") as f:
            f.write("""
def execute():
    return "common execute"

def calculate():
    return 42
""")

        os.makedirs(os.path.join(temp_dir, "service"), exist_ok=True)
        with open(os.path.join(temp_dir, "service", "handler.py"), "w") as f:
            f.write("""
from utils.common import execute

def execute():
    return "handler execute"

def process():
    return execute()
""")

        db = TestingSessionLocal()
        snapshot_id = str(uuid.uuid4())
        
        job = AnalysisJob(id=uuid.uuid4(), snapshot_id=uuid.UUID(snapshot_id), status="PENDING")
        db.add(job)
        db.commit()

        run_analysis_pipeline(db, snapshot_id, temp_dir, job)

        assert job.status == "COMPLETED"
        assert job.current_stage == "COMPLETED"

        files = db.query(File).filter(File.snapshot_id == uuid.UUID(snapshot_id)).all()
        assert len(files) == 2

        execute_entities = db.query(CodeEntity).filter(
            CodeEntity.snapshot_id == uuid.UUID(snapshot_id),
            CodeEntity.name == "execute",
            CodeEntity.type == "function"
        ).all()
        assert len(execute_entities) == 2

        dependencies = db.query(Dependency).filter(
            Dependency.snapshot_id == uuid.UUID(snapshot_id)
        ).all()
        assert len(dependencies) >= 1

        db.close()

def test_polyglot_pipeline_python_and_typescript():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Python Backend Service
        os.makedirs(os.path.join(temp_dir, "backend"), exist_ok=True)
        with open(os.path.join(temp_dir, "backend", "api.py"), "w") as f:
            f.write("""
class ApiService:
    def handle_request(self):
        return self.auth()

    def auth(self):
        return True
""")

        # TypeScript Frontend Component
        os.makedirs(os.path.join(temp_dir, "frontend"), exist_ok=True)
        with open(os.path.join(temp_dir, "frontend", "Dashboard.tsx"), "w") as f:
            f.write("""
import React, { useState } from 'react';

export const renderHeader = () => {
    return "Dashboard Header";
};

export default function Dashboard() {
    const title = renderHeader();
    return title;
}
""")

        db = TestingSessionLocal()
        snapshot_id = str(uuid.uuid4())
        
        job = AnalysisJob(id=uuid.uuid4(), snapshot_id=uuid.UUID(snapshot_id), status="PENDING")
        db.add(job)
        db.commit()

        run_analysis_pipeline(db, snapshot_id, temp_dir, job)

        # 1. Verify Polyglot Files
        files = db.query(File).filter(File.snapshot_id == uuid.UUID(snapshot_id)).all()
        lang_by_path = {f.path: f.language for f in files}
        assert lang_by_path["backend/api.py"] == "python"
        assert lang_by_path["frontend/Dashboard.tsx"] == "typescript"

        # 2. Verify Polyglot Entities
        entities = db.query(CodeEntity).filter(CodeEntity.snapshot_id == uuid.UUID(snapshot_id)).all()
        ent_names = [e.name for e in entities]
        assert "ApiService" in ent_names
        assert "Dashboard" in ent_names
        assert "renderHeader" in ent_names

        # 3. Verify Analysis Findings
        findings = db.query(AnalysisFinding).filter(
            AnalysisFinding.snapshot_id == uuid.UUID(snapshot_id)
        ).all()
        # Some findings should be detected (e.g. dead code for uncalled entities)
        assert len(findings) >= 1

        db.close()
