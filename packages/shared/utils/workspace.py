import tempfile
import os
import shutil
import uuid

WORKSPACES_ROOT = os.getenv("WORKSPACES_ROOT", "/tmp/codeatlas_workspaces")

def get_workspace_dir(snapshot_id: str) -> str:
    path = os.path.join(WORKSPACES_ROOT, str(snapshot_id))
    os.makedirs(path, exist_ok=True)
    return path

def cleanup_workspace(snapshot_id: str):
    path = os.path.join(WORKSPACES_ROOT, str(snapshot_id))
    if os.path.exists(path) and os.path.abspath(path).startswith(os.path.abspath(WORKSPACES_ROOT)):
        shutil.rmtree(path, ignore_errors=True)
