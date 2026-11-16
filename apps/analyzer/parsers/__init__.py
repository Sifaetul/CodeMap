import os
from typing import Optional, Any
from apps.analyzer.parsers.python_parser import PythonParser
from apps.analyzer.parsers.javascript_parser import JavaScriptParser

_python_parser = PythonParser()
_javascript_parser = JavaScriptParser()

PYTHON_EXTENSIONS = {".py"}
JAVASCRIPT_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}

def get_parser_for_path(path: str) -> Optional[Any]:
    ext = os.path.splitext(path)[1].lower()
    if ext in PYTHON_EXTENSIONS:
        return _python_parser
    elif ext in JAVASCRIPT_EXTENSIONS:
        return _javascript_parser
    return None

def detect_language(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in PYTHON_EXTENSIONS:
        return "python"
    elif ext in {".ts", ".tsx"}:
        return "typescript"
    elif ext in {".js", ".jsx", ".mjs", ".cjs"}:
        return "javascript"
    return "unknown"
