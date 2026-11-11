import subprocess
import re

class GitError(Exception):
    pass

def validate_github_url(url: str) -> bool:
    pattern = r'^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?$'
    return bool(re.match(pattern, url))

def clone_repository(url: str, target_dir: str):
    if not validate_github_url(url):
        raise GitError("Invalid GitHub URL format.")
    
    try:
        # Secure subprocess execution without shell=True
        # depth 1 for shallow clone to save time/space
        result = subprocess.run(
            ["git", "clone", "--depth", "1", url, target_dir],
            capture_output=True,
            text=True,
            check=True,
            timeout=300
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise GitError(f"Git clone failed: {e.stderr}")
    except subprocess.TimeoutExpired:
        raise GitError("Git clone timed out.")
