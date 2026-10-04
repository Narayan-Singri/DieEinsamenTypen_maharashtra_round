"""
Variable-state tracer for Re:Learn.
Uses sys.settrace to record step-by-step memory frame snapshots.

Two modes:
  1. trace_code(code, input_val) — Traces solution(input_val) inside a function
  2. trace_arbitrary(code) — Traces arbitrary code execution line-by-line
"""
import sys
import copy
import threading
import textwrap
import io
import contextlib
from typing import Any, Dict, List


TRACE_TIMEOUT = 3.0
MAX_FRAMES = 200   # prevent runaway trace collections


def _safe_copy(val: Any) -> Any:
    """Attempt a deep-copy, fall back to repr string."""
    try:
        return copy.deepcopy(val)
    except Exception:
        return repr(val)


def _safe_repr(val: Any) -> str:
    """Safe string representation of a value."""
    try:
        r = repr(val)
        if len(r) > 200:
            r = r[:200] + "..."
        return r
    except Exception:
        return "<unprintable>"


def _filter_locals(local_vars: dict) -> dict:
    """Filter out internal/dunder variables and callables from a locals dict."""
    result = {}
    for k, v in local_vars.items():
        if k.startswith("__"):
            continue
        if callable(v) and not isinstance(v, (list, dict, set, tuple)):
            continue
        result[k] = _safe_copy(v)
    return result


def trace_code(code: str, input_val: Any = None, timeout: float = TRACE_TIMEOUT) -> List[Dict]:
    """
    Run `solution(input_val)` with sys.settrace attached.
    Returns a list of frame snapshots:
        [
          {
            "event": "line" | "call" | "return",
            "line": int,
            "locals": {"var": value, ...},
            "source_line": str,
          },
          ...
        ]
    """
    frames: List[Dict] = []
    source_lines = textwrap.dedent(code).splitlines()

    safe_builtins = {
        "abs": abs, "all": all, "any": any, "bool": bool, "dict": dict,
        "enumerate": enumerate, "filter": filter, "float": float, "int": int,
        "isinstance": isinstance, "len": len, "list": list, "map": map,
        "max": max, "min": min, "next": next, "print": print, "range": range,
        "reversed": reversed, "round": round, "set": set, "sorted": sorted,
        "str": str, "sum": sum, "tuple": tuple, "type": type, "zip": zip,
        "True": True, "False": False, "None": None,
        "ValueError": ValueError, "TypeError": TypeError,
        "IndexError": IndexError,
    }

    holder: Dict[str, Any] = {"done": False, "error": None}

    def _tracer(frame, event, arg):
        """Trace callback — only record events inside functions named 'solution'."""
        if len(frames) >= MAX_FRAMES:
            return None

        fn_name = frame.f_code.co_name
        if fn_name != "solution":
            return _tracer  # keep tracing to find solution calls

        lineno = frame.f_lineno
        src_line = source_lines[lineno - 1].strip() if 0 < lineno <= len(source_lines) else ""

        local_vars = _filter_locals(frame.f_locals)

        frames.append({
            "event": event,
            "line": lineno,
            "locals": local_vars,
            "source_line": src_line,
        })
        return _tracer

    def _run():
        ns = {"__builtins__": safe_builtins}
        try:
            compiled = compile(textwrap.dedent(code), "<tracer>", "exec")
            exec(compiled, ns)
            fn = ns.get("solution")
            if fn is None:
                holder["error"] = "No solution function"
                return
            arg = list(input_val) if isinstance(input_val, list) else input_val
            sys.settrace(_tracer)
            try:
                fn(arg)
            finally:
                sys.settrace(None)
        except Exception as e:
            holder["error"] = f"{type(e).__name__}: {e}"
        finally:
            holder["done"] = True

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=timeout)

    if not holder["done"]:
        frames.append({"event": "timeout", "line": -1, "locals": {}, "source_line": ""})

    return frames


def trace_arbitrary(code: str, timeout: float = TRACE_TIMEOUT) -> List[Dict]:
    """
    Trace arbitrary Python code (no solution function required).
    Records every line/call/return event.

    Returns a list of frame snapshots:
        [
          {
            "step": int,
            "event": "line" | "call" | "return" | "exception",
            "line": int,
            "locals": {"var": value, ...},
            "source_line": str,
            "function": str | None,
          },
          ...
        ]
    """
    if not code or not code.strip():
        return []

    frames: List[Dict] = []
    source_lines = textwrap.dedent(code).splitlines()
    step_counter = [0]

    safe_builtins = {
        "abs": abs, "all": all, "any": any, "bin": bin, "bool": bool,
        "chr": chr, "dict": dict, "divmod": divmod,
        "enumerate": enumerate, "filter": filter, "float": float,
        "format": format, "frozenset": frozenset,
        "hasattr": hasattr, "hash": hash, "hex": hex,
        "int": int, "isinstance": isinstance, "len": len, "list": list,
        "map": map, "max": max, "min": min, "next": next,
        "oct": oct, "ord": ord, "pow": pow,
        "print": print, "range": range, "repr": repr, "reversed": reversed,
        "round": round, "set": set, "sorted": sorted,
        "str": str, "sum": sum, "tuple": tuple, "type": type,
        "zip": zip,
        "True": True, "False": False, "None": None,
        "ValueError": ValueError, "TypeError": TypeError,
        "IndexError": IndexError, "KeyError": KeyError,
        "ZeroDivisionError": ZeroDivisionError,
        "RuntimeError": RuntimeError,
        "AttributeError": AttributeError,
        "NameError": NameError,
        "input": lambda *a: "",
    }

    holder: Dict[str, Any] = {"done": False, "error": None}

    def _tracer(frame, event, arg):
        """Trace callback for arbitrary code."""
        if len(frames) >= MAX_FRAMES:
            return None

        filename = frame.f_code.co_filename
        # Only trace user code (not builtins/stdlib)
        if filename not in ("<practice_trace>", "<string>"):
            return _tracer

        lineno = frame.f_lineno
        src_line = ""
        if 0 < lineno <= len(source_lines):
            src_line = source_lines[lineno - 1]

        fn_name = frame.f_code.co_name
        if fn_name == "<module>":
            fn_name = None

        local_vars = _filter_locals(frame.f_locals)

        step_counter[0] += 1
        snapshot = {
            "step": step_counter[0],
            "event": event,
            "line": lineno,
            "locals": local_vars,
            "source_line": src_line.strip() if src_line else "",
            "function": fn_name,
        }

        # For return events, capture the return value
        if event == "return" and arg is not None:
            snapshot["return_value"] = _safe_copy(arg)

        frames.append(snapshot)
        return _tracer

    def _run():
        ns = {"__builtins__": safe_builtins}
        stdout_capture = io.StringIO()
        try:
            compiled = compile(textwrap.dedent(code), "<practice_trace>", "exec")
            sys.settrace(_tracer)
            try:
                with contextlib.redirect_stdout(stdout_capture):
                    exec(compiled, ns)
            finally:
                sys.settrace(None)
        except Exception as e:
            # Record the exception as a final frame
            import traceback as tb
            exc_frames = tb.extract_tb(e.__traceback__)
            error_line = None
            for ef in reversed(exc_frames):
                if ef.filename == "<practice_trace>":
                    error_line = ef.lineno
                    break
            frames.append({
                "step": step_counter[0] + 1,
                "event": "exception",
                "line": error_line or -1,
                "locals": {},
                "source_line": f"{type(e).__name__}: {e}",
                "function": None,
            })
        finally:
            holder["done"] = True

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=timeout)

    if not holder["done"]:
        frames.append({
            "step": step_counter[0] + 1,
            "event": "timeout",
            "line": -1,
            "locals": {},
            "source_line": "Execution timed out",
            "function": None,
        })

    return frames


def extract_inspector_data(trace_frames: List[Dict]) -> Dict[str, Any]:
    """
    Extract runtime inspector data from trace frames.
    Returns a snapshot of all variables at the final state, plus
    per-variable type and history information.

    Returns:
        {
          "variables": [
            {
              "name": str,
              "type": str,
              "value": any,
              "display_value": str,
              "scope": "local" | "global",
              "first_seen_step": int,
              "last_modified_step": int,
            },
            ...
          ],
          "total_steps": int,
          "has_functions": bool,
          "functions": [str, ...],
        }
    """
    if not trace_frames:
        return {
            "variables": [],
            "total_steps": 0,
            "has_functions": False,
            "functions": [],
        }

    # Track variable history
    var_history: Dict[str, Dict] = {}
    functions_seen = set()

    for frame in trace_frames:
        step = frame.get("step", 0)
        fn = frame.get("function")
        if fn:
            functions_seen.add(fn)

        for var_name, var_val in frame.get("locals", {}).items():
            if var_name not in var_history:
                var_history[var_name] = {
                    "name": var_name,
                    "first_seen_step": step,
                    "last_modified_step": step,
                    "value": var_val,
                    "scope": "local" if fn else "global",
                }
            else:
                existing = var_history[var_name]
                # Check if value changed
                try:
                    changed = var_val != existing["value"]
                except Exception:
                    changed = True
                if changed:
                    existing["last_modified_step"] = step
                    existing["value"] = var_val

    # Build final variable list
    variables = []
    for vname, vinfo in var_history.items():
        val = vinfo["value"]
        try:
            type_name = type(val).__name__
        except Exception:
            type_name = "unknown"

        display_val = _safe_repr(val)

        variables.append({
            "name": vname,
            "type": type_name,
            "value": val,
            "display_value": display_val,
            "scope": vinfo["scope"],
            "first_seen_step": vinfo["first_seen_step"],
            "last_modified_step": vinfo["last_modified_step"],
        })

    return {
        "variables": variables,
        "total_steps": len(trace_frames),
        "has_functions": len(functions_seen) > 0,
        "functions": list(functions_seen),
    }
