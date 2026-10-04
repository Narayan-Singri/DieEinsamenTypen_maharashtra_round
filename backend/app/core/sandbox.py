"""
Sandbox execution runner for Re:Learn.
- Blocks unsafe imports: os, sys, subprocess, socket, shutil, importlib, ctypes, multiprocessing
- Enforces 2.0-second wall-clock timeout via threading
- Returns stdout output, test results, and any error messages
- Supports both solution-function mode (predefined problems) and arbitrary code mode (practice)
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
    "ZeroDivisionError": ZeroDivisionError,
    "RuntimeError": RuntimeError,
    "AttributeError": AttributeError,
    "NameError": NameError,
    "input": lambda *a: "",  # stub input() to prevent blocking
}


# ---------------------------------------------------------------------------
# Core runner — solution-function mode (predefined problems)
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


# ---------------------------------------------------------------------------
# Arbitrary code runner — Practice mode
# ---------------------------------------------------------------------------

def run_arbitrary_code(
    code: str,
    timeout: float = TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    """
    Execute arbitrary Python code in the sandbox (no test cases, no solution function needed).
    Used for Practice mode where users write any code they want.

    Returns:
        {
          "stdout": str,
          "stderr": str,
          "status": "success" | "error" | "timeout" | "syntax_error",
          "error": str | None,
          "error_line": int | None,
          "error_type": str | None,
          "namespace": dict  (safe variables, no builtins/callables)
        }
    """
    # Handle empty code
    if not code or not code.strip():
        return {
            "stdout": "",
            "stderr": "",
            "status": "error",
            "error": "No code provided.",
            "error_line": None,
            "error_type": "EmptyCode",
            "namespace": {},
        }

    # 1. AST-level import check
    try:
        _check_blocked_imports(code)
    except ValueError as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "status": "error",
            "error": str(e),
            "error_line": None,
            "error_type": "BlockedImport",
            "namespace": {},
        }
    except SyntaxError as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "status": "syntax_error",
            "error": str(e),
            "error_line": getattr(e, "lineno", None),
            "error_type": "SyntaxError",
            "namespace": {},
        }

    # 2. Compile
    try:
        compiled = compile(code, "<practice_code>", "exec")
    except SyntaxError as e:
        return {
            "stdout": "",
            "stderr": f"SyntaxError: {e}",
            "status": "syntax_error",
            "error": f"SyntaxError: {e}",
            "error_line": e.lineno,
            "error_type": "SyntaxError",
            "namespace": {},
        }

    # 3. Execute with timeout
    result_holder: Dict[str, Any] = {"done": False, "error": None, "namespace": {}}
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    def _exec():
        ns = {"__builtins__": SAFE_BUILTINS}
        try:
            with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                exec(compiled, ns)
            result_holder["namespace"] = ns
        except Exception as e:
            result_holder["error"] = f"{type(e).__name__}: {e}"
            result_holder["error_type"] = type(e).__name__
            # Try to get line number from traceback
            import traceback as tb
            frames = tb.extract_tb(e.__traceback__)
            error_line = None
            for frame in reversed(frames):
                if frame.filename == "<practice_code>":
                    error_line = frame.lineno
                    break
            result_holder["error_line"] = error_line
        finally:
            result_holder["done"] = True

    thread = threading.Thread(target=_exec, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if not result_holder["done"]:
        return {
            "stdout": stdout_capture.getvalue(),
            "stderr": "",
            "status": "timeout",
            "error": f"Execution timed out after {timeout}s (possible infinite loop)",
            "error_line": None,
            "error_type": "Timeout",
            "namespace": {},
        }

    if result_holder["error"]:
        return {
            "stdout": stdout_capture.getvalue(),
            "stderr": result_holder["error"],
            "status": "error",
            "error": result_holder["error"],
            "error_line": result_holder.get("error_line"),
            "error_type": result_holder.get("error_type", "RuntimeError"),
            "namespace": {},
        }

    # Extract safe variables from namespace (exclude builtins/callables/dunders)
    ns = result_holder["namespace"]
    safe_ns = {}
    for k, v in ns.items():
        if k.startswith("__") or callable(v):
            continue
        try:
            # Ensure it's serialisable
            repr(v)
            safe_ns[k] = v
        except Exception:
            safe_ns[k] = repr(v)

    return {
        "stdout": stdout_capture.getvalue(),
        "stderr": stderr_capture.getvalue(),
        "status": "success",
        "error": None,
        "error_line": None,
        "error_type": None,
        "namespace": safe_ns,
    }
