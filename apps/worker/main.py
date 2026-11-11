import os
from celery import Celery
from packages.shared.database import SessionLocal
from packages.shared.models import AnalysisJob
from apps.analyzer.pipeline import run_analysis_pipeline

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("codeatlas_worker", broker=redis_url, backend=redis_url)

@celery_app.task
def analyze_repository_task(job_id: str, snapshot_id: str, workspace_dir: str):
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            return
        
        job.status = "RUNNING"
        db.commit()

        # Run pipeline
        run_analysis_pipeline(db, snapshot_id, workspace_dir, job)

        job.status = "COMPLETED"
        job.progress = "100%"
        db.commit()
    except Exception as e:
        job.status = "FAILED"
        job.error_message = str(e)
        db.commit()
    finally:
        db.close()
