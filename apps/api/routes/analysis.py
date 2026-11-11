from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from apps.api.core.deps import get_db, get_current_user
from packages.shared.models import AnalysisJob, User

router = APIRouter()

@router.get("/{job_id}")
def get_job_status(job_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # For a real app, verify user has access to job's snapshot's repository's project
    return job
