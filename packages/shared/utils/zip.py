import zipfile
import os

class ZipExtractionError(Exception):
    pass

MAX_ZIP_SIZE = 50 * 1024 * 1024 # 50 MB
MAX_EXTRACTED_SIZE = 200 * 1024 * 1024 # 200 MB

def is_safe_path(target_path: str, base_dir: str) -> bool:
    abs_target = os.path.abspath(target_path)
    abs_base = os.path.abspath(base_dir)
    return abs_target.startswith(abs_base)

def extract_zip(file_path: str, target_dir: str):
    if os.path.getsize(file_path) > MAX_ZIP_SIZE:
        raise ZipExtractionError("ZIP file exceeds maximum allowed size.")

    extracted_size = 0
    with zipfile.ZipFile(file_path, "r") as zf:
        for zip_info in zf.infolist():
            extracted_size += zip_info.file_size
            if extracted_size > MAX_EXTRACTED_SIZE:
                raise ZipExtractionError("Extracted contents exceed maximum allowed size.")
            
            target_path = os.path.join(target_dir, zip_info.filename)
            if not is_safe_path(target_path, target_dir):
                raise ZipExtractionError("Path traversal attempt detected in ZIP.")
                
            zf.extract(zip_info, target_dir)
