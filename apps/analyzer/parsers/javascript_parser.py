import re
from typing import List, Dict, Any, Optional

class JavaScriptParser:
    """
    Fast and robust parser for JavaScript & TypeScript source code.
    Extracts imports, classes, functions, arrow functions, and calls with line numbers.
    """

    # Import Patterns
    IMPORT_ESM_PATTERN = re.compile(
        r'''import\s+(?:(?P<default>[\w$]+)\s*,?\s*)?(?:\{\s*(?P<named>[^}]+)\s*\}|\*\s+as\s+(?P<namespace>[\w$]+))?\s*(?:from\s*)?['"](?P<source>[^'"]+)['"]''',
        re.MULTILINE
    )
    IMPORT_REQUIRE_PATTERN = re.compile(
        r'''(?:const|let|var)\s+(?:\{(?P<named>[^}]+)\}|(?P<ident>[\w$]+))\s*=\s*require\s*\(\s*['"](?P<source>[^'"]+)['"]\s*\)''',
        re.MULTILINE
    )

    # Class Pattern: class Name [extends Base] {
    CLASS_PATTERN = re.compile(
        r'''(?:export\s+(?:default\s+)?)?class\s+(?P<name>[\w$]+)(?:\s+extends\s+(?P<extends>[\w$]+))?(?:\s+implements\s+[^{]+)?\s*\{''',
        re.MULTILINE
    )

    # Function Patterns:
    # 1. Standard function: [export [default]] [async] function name(args) {
    FUNC_DECL_PATTERN = re.compile(
        r'''(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s*(?P<name>[\w$]+)?\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{''',
        re.MULTILINE
    )

    # 2. Variable function: [export] const/let/var name = [async] (args) => { or function(args) {
    FUNC_VAR_PATTERN = re.compile(
        r'''(?:export\s+)?(?:const|let|var)\s+(?P<name>[\w$]+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[\w$]+)\s*(?::\s*[^=]+)?=>\s*\{?''',
        re.MULTILINE
    )

    # Call Pattern: identifier(
    CALL_PATTERN = re.compile(
        r'''(?:(?P<obj>[\w$]+)\.)?(?P<call>[\w$]+)\s*\(''',
        re.MULTILINE
    )

    RESERVED_CALLS = {
        "if", "for", "while", "switch", "catch", "return", "typeof", "require",
        "import", "function", "constructor", "super"
    }

    def parse(self, file_content: str, file_path: str) -> Dict[str, Any]:
        entities: List[Dict[str, Any]] = []
        imports: List[Dict[str, Any]] = []
        calls: List[Dict[str, Any]] = []

        lines = file_content.splitlines()
        
        # 1. Extract Imports
        # ESM imports
        for match in self.IMPORT_ESM_PATTERN.finditer(file_content):
            source = match.group("source")
            line_no = file_content[:match.start()].count("\n") + 1
            
            # Check named imports
            named = match.group("named")
            if named:
                for item in named.split(","):
                    clean = item.strip().split(" as ")[-1].strip()
                    if clean:
                        imports.append({"name": f"{source}.{clean}", "module": source, "line": line_no})
            
            default = match.group("default")
            if default:
                imports.append({"name": f"{source}.{default}", "module": source, "line": line_no})

            namespace = match.group("namespace")
            if namespace:
                imports.append({"name": f"{source}.{namespace}", "module": source, "line": line_no})

            if not named and not default and not namespace:
                imports.append({"name": source, "module": source, "line": line_no})

        # CommonJS require() imports
        for match in self.IMPORT_REQUIRE_PATTERN.finditer(file_content):
            source = match.group("source")
            line_no = file_content[:match.start()].count("\n") + 1
            ident = match.group("ident")
            if ident:
                imports.append({"name": f"{source}.{ident}", "module": source, "line": line_no})
            named = match.group("named")
            if named:
                for item in named.split(","):
                    clean = item.strip().split(" as ")[-1].strip()
                    if clean:
                        imports.append({"name": f"{source}.{clean}", "module": source, "line": line_no})

        # 2. Extract Classes
        for match in self.CLASS_PATTERN.finditer(file_content):
            class_name = match.group("name")
            start_line = file_content[:match.start()].count("\n") + 1
            end_line = self._find_closing_brace_line(file_content, match.end() - 1, start_line)
            
            entities.append({
                "name": class_name,
                "type": "class",
                "start_line": start_line,
                "end_line": end_line,
                "extends": match.group("extends")
            })

        # 3. Extract Function Declarations
        for match in self.FUNC_DECL_PATTERN.finditer(file_content):
            func_name = match.group("name") or "anonymous"
            start_line = file_content[:match.start()].count("\n") + 1
            end_line = self._find_closing_brace_line(file_content, match.end() - 1, start_line)
            
            entities.append({
                "name": func_name,
                "type": "function",
                "start_line": start_line,
                "end_line": end_line,
            })

        # 4. Extract Arrow / Variable Functions
        for match in self.FUNC_VAR_PATTERN.finditer(file_content):
            func_name = match.group("name")
            start_line = file_content[:match.start()].count("\n") + 1
            # Check if it has a body block
            if "{" in file_content[match.start():match.end() + 2]:
                brace_pos = file_content.find("{", match.start())
                end_line = self._find_closing_brace_line(file_content, brace_pos, start_line)
            else:
                end_line = start_line

            entities.append({
                "name": func_name,
                "type": "function",
                "start_line": start_line,
                "end_line": end_line,
            })

        # Sort entities by start_line
        entities.sort(key=lambda x: x["start_line"])

        # 5. Extract Calls within Entities
        for ent in entities:
            ent_start = ent["start_line"]
            ent_end = ent["end_line"]
            
            # Slice entity content lines
            ent_lines = lines[ent_start - 1 : ent_end]
            ent_text = "\n".join(ent_lines)
            
            for call_match in self.CALL_PATTERN.finditer(ent_text):
                callee = call_match.group("call")
                if callee not in self.RESERVED_CALLS:
                    rel_line = ent_text[:call_match.start()].count("\n")
                    calls.append({
                        "caller": ent["name"],
                        "callee": callee,
                        "line": ent_start + rel_line
                    })

        return {
            "entities": entities,
            "imports": imports,
            "calls": calls
        }

    def _find_closing_brace_line(self, content: str, open_brace_idx: int, start_line: int) -> int:
        """Finds line number of matching closing brace accounting for strings and nesting."""
        depth = 0
        in_string = None
        i = open_brace_idx
        n = len(content)
        
        while i < n:
            char = content[i]
            
            # Skip escapes inside strings
            if in_string:
                if char == '\\':
                    i += 2
                    continue
                elif char == in_string:
                    in_string = None
            else:
                if char in ("'", '"', '`'):
                    in_string = char
                elif char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        return content[:i].count("\n") + 1
            i += 1
            
        return start_line + content[open_brace_idx:].count("\n")
