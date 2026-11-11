from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
import redis
from sqlalchemy import create_engine
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from apps.api.routes import auth, projects, repositories, analysis, graph, chat

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/codeatlas"
    REDIS_URL: str = "redis://localhost:6379/0"

settings = Settings()

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="CodeAtlas API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(repositories.router, prefix="/api/projects", tags=["repositories"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(graph.router, prefix="/api/projects", tags=["graph"])
app.include_router(chat.router, prefix="/api/projects", tags=["chat"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "api"}

@app.get("/ready")
def readiness_check():
    checks = {"database": "disconnected", "redis": "disconnected"}
    status_code = 200
    
    # Check Database
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        status_code = 503

    # Check Redis
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        checks["redis"] = "connected"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"
        status_code = 503

    response = {"status": "ready" if status_code == 200 else "not_ready", "checks": checks}
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
