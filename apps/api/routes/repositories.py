from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from uuid import UUID
import shutil
import os
from celery import Celery

from packages.shared.models import Project, User, Repository, RepositorySnapshot, AnalysisJob
from apps.api.schemas.repository import GithubImportRequest, RepositoryResponse
from apps.api.core.deps import get_db, get_current_user
from packages.shared.utils.workspace import get_workspace_dir
from packages.shared.utils.git import clone_repository, GitError, validate_github_url
from packages.shared.utils.zip import extract_zip, ZipExtractionError

router = APIRouter()

# Initialize celery client to send tasks without importing the worker module
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_client = Celery("codeatlas_api", broker=redis_url)

def verify_project_access(project_id: UUID, db: Session, user: User) -> Project:
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/{project_id}/repositories/github", response_model=RepositoryResponse)
def import_github_repository(
    project_id: UUID,
    request: GithubImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = verify_project_access(project_id, db, current_user)
    
    if not validate_github_url(request.url):
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")

    repo = db.query(Repository).filter(Repository.project_id == project.id, Repository.url == request.url).first()
    if not repo:
        repo = Repository(project_id=project.id, url=request.url, source_type="github")
        db.add(repo)
        db.commit()
        db.refresh(repo)

    snapshot = RepositorySnapshot(repository_id=repo.id)
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    workspace_dir = get_workspace_dir(str(snapshot.id))
    try:
        clone_repository(request.url, workspace_dir)
    except GitError as e:
        db.delete(snapshot)
        db.commit()
        raise HTTPException(status_code=400, detail=str(e))

    # Trigger Analysis Job automatically
    job = AnalysisJob(snapshot_id=snapshot.id, status="PENDING")
    db.add(job)
    db.commit()
    db.refresh(job)

    # Use send_task to avoid importing worker code
    task = celery_client.send_task(
        "apps.worker.main.analyze_repository_task",
        args=[str(job.id), str(snapshot.id), workspace_dir]
    )
    try:
        task.get(timeout=30)
    except Exception as e:
        pass

    return repo

@router.post("/{project_id}/repositories/upload", response_model=RepositoryResponse)
def upload_zip_repository(
    project_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = verify_project_access(project_id, db, current_user)
    
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported")

    repo = Repository(project_id=project.id, url=file.filename, source_type="zip")
    db.add(repo)
    db.commit()
    db.refresh(repo)

    snapshot = RepositorySnapshot(repository_id=repo.id)
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    workspace_dir = get_workspace_dir(str(snapshot.id))
    temp_zip_path = os.path.join(workspace_dir, "upload.zip")
    
    try:
        with open(temp_zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        extract_zip(temp_zip_path, workspace_dir)
        os.remove(temp_zip_path)
    except Exception as e:
        db.delete(snapshot)
        db.commit()
        raise HTTPException(status_code=400, detail=f"Failed to process ZIP: {str(e)}")

    # Trigger Analysis Job automatically
    job = AnalysisJob(snapshot_id=snapshot.id, status="PENDING")
    db.add(job)
    db.commit()
    db.refresh(job)

    task = celery_client.send_task(
        "apps.worker.main.analyze_repository_task",
        args=[str(job.id), str(snapshot.id), workspace_dir]
    )
    try:
        task.get(timeout=30)
    except Exception as e:
        pass

    return repo
