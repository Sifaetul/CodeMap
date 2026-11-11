import os
from typing import List, Dict

IGNORE_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build"}

class RepositoryScanner:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir

    def scan(self) -> Dict[str, List[str]]:
        """Scans the workspace and returns a dictionary mapping file extensions to a list of relative file paths."""
        files_by_ext = {}
        for root, dirs, files in os.walk(self.workspace_dir):
            # Mutate dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                rel_path = os.path.relpath(os.path.join(root, file), self.workspace_dir)
                if ext not in files_by_ext:
                    files_by_ext[ext] = []
                files_by_ext[ext].append(rel_path)
                
        return files_by_ext
