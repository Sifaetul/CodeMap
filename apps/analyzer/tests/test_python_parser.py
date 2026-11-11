import pytest
from apps.analyzer.parsers.python_parser import PythonParser

def test_python_parser_advanced():
    code = """
import os
from sys import argv
import json as j

class Engine:
    def start(self):
        self.init()

def main():
    e = Engine()
    e.start()
    print("Done")
"""
    parser = PythonParser()
    result = parser.parse(code, "test.py")
    
    # Check Imports
    imports = result["imports"]
    assert len(imports) == 3
    import_names = [i["name"] for i in imports]
    assert "os" in import_names
    assert "sys.argv" in import_names
    assert "json" in import_names
    
    # Check Entities
    entities = result["entities"]
    assert len(entities) == 3 # Engine, start, main
    
    # Check Calls
    calls = result["calls"]
    # We expect 'start' to call 'init'
    # We expect 'main' to call 'Engine', 'start', 'print'
    assert len(calls) == 4
    
    main_calls = [c["callee"] for c in calls if c["caller"] == "main"]
    assert "Engine" in main_calls
    assert "start" in main_calls
    assert "print" in main_calls
    
    start_calls = [c["callee"] for c in calls if c["caller"] == "start"]
    assert "init" in start_calls
