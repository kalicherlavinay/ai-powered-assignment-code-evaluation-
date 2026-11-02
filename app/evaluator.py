"""Python assignment feature extraction and test-case execution."""
import ast
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def analyze_source(source: str) -> tuple[dict[str, int], str | None]:
    lines = [line for line in source.splitlines() if line.strip()]
    try:
        tree = ast.parse(source)
        syntax_valid = 1
        functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        loops = [n for n in ast.walk(tree) if isinstance(n, (ast.For, ast.AsyncFor, ast.While))]
        branches = [n for n in ast.walk(tree) if isinstance(n, (ast.If, ast.IfExp, ast.Match))]
        docs = sum(bool(ast.get_docstring(n)) for n in functions)
        error = None
    except SyntaxError as exc:
        syntax_valid, functions, loops, branches, docs = 0, [], [], [], 0
        error = f"Syntax error on line {exc.lineno}: {exc.msg}"
    return {
        "passed_tests": 0, "total_tests": 0, "syntax_valid": syntax_valid,
        "line_count": len(lines), "function_count": len(functions),
        "loop_count": len(loops), "branch_count": len(branches), "docstring_count": docs,
    }, error


def run_cases(source: str, function_name: str, cases: list[dict], timeout_seconds: float = 3.0) -> list[dict]:
    """Run in a short-lived child process with a timeout; this is not a secure sandbox."""
    runner = r'''import json, sys, traceback
payload=json.loads(sys.stdin.read())
source=payload["source"]
name=payload["function_name"]
cases=payload["cases"]
namespace={"__builtins__": {"abs":abs,"all":all,"any":any,"bool":bool,"dict":dict,"enumerate":enumerate,"float":float,"int":int,"len":len,"list":list,"max":max,"min":min,"print":print,"range":range,"reversed":reversed,"set":set,"sorted":sorted,"str":str,"sum":sum,"tuple":tuple,"zip":zip,"ValueError":ValueError,"TypeError":TypeError,"Exception":Exception}}
try:
    exec(compile(source, "<student-submission>", "exec"), namespace, namespace)
    fn=namespace[name]
    results=[]
    for case in cases:
        try:
            actual=fn(*case.get("args", []), **case.get("kwargs", {}))
            passed=(actual == case.get("expected"))
            results.append({"passed":bool(passed),"expected":case.get("expected"),"actual":actual if isinstance(actual,(str,int,float,bool,type(None),list,dict)) else repr(actual)})
        except Exception as e:
            results.append({"passed":False,"expected":case.get("expected"),"error":type(e).__name__+": "+str(e)})
    print(json.dumps(results))
except Exception as e:
    print(json.dumps({"error":type(e).__name__+": "+str(e)}))
'''
    payload = json.dumps({"source": source, "function_name": function_name, "cases": cases})
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8"}
    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-c", runner], input=payload, text=True,
            capture_output=True, timeout=timeout_seconds, env=env,
            cwd=tempfile.gettempdir(), check=False,
        )
        if completed.returncode != 0:
            return [{"passed": False, "error": "Submission process failed."} for _ in cases]
        parsed = json.loads(completed.stdout)
        if isinstance(parsed, dict):
            return [{"passed": False, "error": parsed.get("error", "Execution failed.")} for _ in cases]
        return parsed
    except subprocess.TimeoutExpired:
        return [{"passed": False, "error": f"Timed out after {timeout_seconds:g} seconds."} for _ in cases]
    except (json.JSONDecodeError, OSError):
        return [{"passed": False, "error": "Could not read the submission result."} for _ in cases]
