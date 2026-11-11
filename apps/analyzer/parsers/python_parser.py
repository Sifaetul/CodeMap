import ast
from typing import List, Dict, Any

class PythonParser:
    def parse(self, file_content: str, file_path: str) -> Dict[str, Any]:
        """Parses Python source code and extracts classes, functions, imports, and calls."""
        entities = []
        imports = []
        calls = []
        
        try:
            tree = ast.parse(file_content, filename=file_path)
            
            # First pass: collect entities and imports
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({"name": alias.name, "line": node.lineno})
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        full_name = f"{module}.{alias.name}" if module else alias.name
                        imports.append({"name": full_name, "line": node.lineno})
            
            # Second pass: walk the tree for classes/functions and their internal calls
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    entities.append({
                        "name": node.name,
                        "type": "class",
                        "docstring": ast.get_docstring(node),
                        "start_line": node.lineno,
                        "end_line": getattr(node, "end_lineno", node.lineno),
                    })
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_name = node.name
                    entities.append({
                        "name": func_name,
                        "type": "function",
                        "docstring": ast.get_docstring(node),
                        "start_line": node.lineno,
                        "end_line": getattr(node, "end_lineno", node.lineno),
                    })
                    
                    # Look for calls inside this function
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            callee_name = None
                            if isinstance(child.func, ast.Name):
                                callee_name = child.func.id
                            elif isinstance(child.func, ast.Attribute):
                                callee_name = child.func.attr
                                
                            if callee_name:
                                calls.append({
                                    "caller": func_name,
                                    "callee": callee_name,
                                    "line": child.lineno
                                })
                                
        except SyntaxError:
            pass
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            
        return {
            "entities": entities,
            "imports": imports,
            "calls": calls
        }
