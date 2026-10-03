"""
Variable-state tracer for Re:Learn.
Uses sys.settrace to record step-by-step memory frame snapshots at each
loop iteration inside the learner's `solution` function.
"""
import sys
import copy
import threading
import textwrap
from typing import Any, Dict, List


TRACE_TIMEOUT = 3.0
MAX_FRAMES = 200   # prevent runaway trace collections


def _safe_copy(val: Any) -> Any:
    """Attempt a deep-copy, fall back to repr string."""
    try:
        return copy.deepcopy(val)
    except Exception:
        return repr(val)


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

        # Filter out internal dunder vars
        local_vars = {
            k: _safe_copy(v)
            for k, v in frame.f_locals.items()
            if not k.startswith("__")
        }

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
