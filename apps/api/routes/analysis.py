from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Dict, Any
from apps.api.core.deps import get_db, get_current_user
from packages.shared.models import AnalysisJob, User, Project, Repository, RepositorySnapshot, AnalysisFinding

router = APIRouter()

@router.get("/{job_id}")
def get_job_status(job_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/projects/{project_id}/findings")
def get_project_findings(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    snapshot = db.query(RepositorySnapshot).join(Repository).filter(Repository.project_id == project.id).order_by(RepositorySnapshot.created_at.desc()).first()
    if not snapshot:
        return []

    findings = db.query(AnalysisFinding).filter(AnalysisFinding.snapshot_id == snapshot.id).all()
    return [
        {
            "id": str(f.id),
            "type": f.type,
            "severity": f.severity,
            "description": f.description,
            "confidence": f.confidence,
            "evidence": f.evidence
        }
        for f in findings
    ]
