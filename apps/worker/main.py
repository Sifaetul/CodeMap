import os
from celery import Celery
from packages.shared.database import SessionLocal
from packages.shared.models import AnalysisJob
from packages.shared.utils.git import clone_repository, GitError
from packages.shared.utils.workspace import cleanup_workspace
from apps.analyzer.pipeline import run_analysis_pipeline

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("codeatlas_worker", broker=redis_url, backend=redis_url)

@celery_app.task
def analyze_repository_task(job_id: str, snapshot_id: str, workspace_dir: str, clone_url: str = None):
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            return
        
        job.status = "RUNNING"
        db.commit()

        # If remote git clone is requested, perform clone asynchronously in worker
        if clone_url:
            job.current_stage = "CLONING"
            job.progress = "5%"
            db.commit()
            clone_repository(clone_url, workspace_dir)

        # Run pipeline
        run_analysis_pipeline(db, snapshot_id, workspace_dir, job)

        job.status = "COMPLETED"
        job.progress = "100%"
        db.commit()
    except Exception as e:
        # Prevent PendingRollbackError by explicitly rolling back aborted transaction
        db.rollback()
        try:
            job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
            if job:
                job.status = "FAILED"
                job.error_message = str(e)
                db.commit()
        except Exception as commit_err:
            print(f"Failed to record job failure in database: {commit_err}")
    finally:
        db.close()
