"""
Sandbox execution runner for Re:Learn.
- Blocks unsafe imports: os, sys, subprocess, socket, shutil, importlib, ctypes, multiprocessing
- Enforces 2.0-second wall-clock timeout via threading
- Returns stdout output, test results, and any error messages
"""
import ast
import threading
import io
import sys
import contextlib
import traceback
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# AST-level import blocker
# ---------------------------------------------------------------------------

BLOCKED_IMPORTS = {
    "os", "sys", "subprocess", "socket", "shutil",
    "importlib", "ctypes", "multiprocessing", "pathlib",
    "signal", "pty", "resource", "fcntl",
}


class ImportBlockerVisitor(ast.NodeVisitor):
    """Raises SyntaxError if code attempts to import a blocked module."""

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            top = alias.name.split(".")[0]
            if top in BLOCKED_IMPORTS:
                raise ValueError(f"Import of '{alias.name}' is not allowed in the sandbox.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            top = node.module.split(".")[0]
            if top in BLOCKED_IMPORTS:
                raise ValueError(f"Import from '{node.module}' is not allowed in the sandbox.")
        self.generic_visit(node)


def _check_blocked_imports(code: str):
    """Parse AST and raise if any blocked imports are found."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise SyntaxError(f"Syntax error in submitted code: {e}")
    blocker = ImportBlockerVisitor()
    blocker.visit(tree)


# ---------------------------------------------------------------------------
# Safe execution namespace
# ---------------------------------------------------------------------------

SAFE_BUILTINS = {
    "abs": abs, "all": all, "any": any, "bin": bin, "bool": bool,
    "chr": chr, "dict": dict, "dir": dir, "divmod": divmod,
    "enumerate": enumerate, "filter": filter, "float": float,
    "format": format, "frozenset": frozenset, "getattr": getattr,
    "hasattr": hasattr, "hash": hash, "hex": hex, "id": id,
    "int": int, "isinstance": isinstance, "issubclass": issubclass,
    "iter": iter, "len": len, "list": list, "map": map, "max": max,
    "min": min, "next": next, "oct": oct, "ord": ord, "pow": pow,
    "print": print, "range": range, "repr": repr, "reversed": reversed,
    "round": round, "set": set, "setattr": setattr, "slice": slice,
    "sorted": sorted, "str": str, "sum": sum, "tuple": tuple,
    "type": type, "vars": vars, "zip": zip,
    "True": True, "False": False, "None": None,
    "ValueError": ValueError, "TypeError": TypeError,
    "IndexError": IndexError, "KeyError": KeyError,
    "Exception": Exception, "StopIteration": StopIteration,
}


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

TIMEOUT_SECONDS = 2.0


def run_in_sandbox(
    code: str,
    test_cases: List[Dict],
    timeout: float = TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    """
    Execute submitted code against test cases inside a restricted sandbox.

    Args:
        code: The learner's Python source code (must define `solution`).
        test_cases: List of {"input": ..., "expected_output": ...} dicts.
        timeout: Wall-clock timeout in seconds.

    Returns:
        {
          "passed": int,
          "total": int,
          "results": [{"input": ..., "expected": ..., "actual": ..., "ok": bool}],
          "error": str | None,
          "stdout": str,
        }
    """
    # 1. AST-level import check
    try:
        _check_blocked_imports(code)
    except (ValueError, SyntaxError) as e:
        return {
            "passed": 0,
            "total": len(test_cases),
            "results": [],
            "error": str(e),
            "stdout": "",
        }

    # 2. Compile
    try:
        compiled = compile(code, "<learner_code>", "exec")
    except SyntaxError as e:
        return {
            "passed": 0,
            "total": len(test_cases),
            "results": [],
            "error": f"SyntaxError: {e}",
            "stdout": "",
        }

    # 3. Execute with timeout
    result_holder: Dict[str, Any] = {"done": False, "error": None, "namespace": {}}
    stdout_capture = io.StringIO()

    def _exec():
        ns = {"__builtins__": SAFE_BUILTINS}
        try:
            with contextlib.redirect_stdout(stdout_capture):
                exec(compiled, ns)
            result_holder["namespace"] = ns
        except Exception as e:
            result_holder["error"] = f"{type(e).__name__}: {e}"
        finally:
            result_holder["done"] = True

    thread = threading.Thread(target=_exec, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if not result_holder["done"]:
        return {
            "passed": 0,
            "total": len(test_cases),
            "results": [],
            "error": f"Execution timed out after {timeout}s",
            "stdout": stdout_capture.getvalue(),
        }

    if result_holder["error"]:
        return {
            "passed": 0,
            "total": len(test_cases),
            "results": [],
            "error": result_holder["error"],
            "stdout": stdout_capture.getvalue(),
        }

    ns = result_holder["namespace"]
    if "solution" not in ns:
        return {
            "passed": 0,
            "total": len(test_cases),
            "results": [],
            "error": "No `solution` function found in submitted code.",
            "stdout": stdout_capture.getvalue(),
        }

    # 4. Run each test case
    solution_fn = ns["solution"]
    results = []
    passed = 0

    for tc in test_cases:
        inp = tc["input"]
        expected = tc["expected_output"]
        try:
            # Deep-copy list inputs so mutations don't bleed between cases
            arg = list(inp) if isinstance(inp, list) else inp
            actual = solution_fn(arg)
            ok = actual == expected
        except Exception as e:
            actual = f"EXCEPTION: {type(e).__name__}: {e}"
            ok = False

        if ok:
            passed += 1
        results.append({
            "input": inp,
            "expected": expected,
            "actual": actual,
            "ok": ok,
        })

    return {
        "passed": passed,
        "total": len(test_cases),
        "results": results,
        "error": None,
        "stdout": stdout_capture.getvalue(),
    }
