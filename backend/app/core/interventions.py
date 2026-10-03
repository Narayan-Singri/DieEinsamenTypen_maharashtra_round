"""
Socratic code annotations and visual memory-state builders for Re:Learn.
Generates contextual explanation strings and visual trace data for the frontend.
"""
from typing import Any, Dict, List


INTERVENTION_TEMPLATES = {
    "M0": {
        "badge": "✅ CORRECT",
        "color": "#22c55e",
        "message": (
            "Great work! Your solution correctly accumulates the result. "
            "Notice how the accumulator variable grows across each iteration."
        ),
        "hint": None,
    },
    "M1": {
        "badge": "⚠️ M1: Accumulator Reinit",
        "color": "#f97316",
        "message": (
            "It looks like your accumulator is being **reset to 0 inside the loop**. "
            "This means only the last element's contribution is kept!"
        ),
        "hint": (
            "Move the initialisation (`s = 0`) to **before** the `for` loop. "
            "The accumulator should only be set once."
        ),
    },
    "M2": {
        "badge": "⚠️ M2: Print vs Return",
        "color": "#a855f7",
        "message": (
            "Your function uses `print()` to output the result, but the calling code "
            "expects a **return value**. `print()` displays output but does not return it — "
            "the function returns `None` by default."
        ),
        "hint": "Replace `print(result)` with `return result` at the end of your function.",
    },
    "M3": {
        "badge": "⚠️ M3: Off-by-One Range",
        "color": "#eab308",
        "message": (
            "Using `range(len(nums) - 1)` stops **one element early**, "
            "skipping the last item in the list."
        ),
        "hint": "Use `range(len(nums))` to include all elements.",
    },
    "M4": {
        "badge": "⚠️ M4: Wrong Comparator",
        "color": "#ef4444",
        "message": (
            "Your comparison direction is inverted. Using `if n < m: m = n` finds "
            "the **minimum**, not the maximum."
        ),
        "hint": "Change `<` to `>` to correctly find the maximum value.",
    },
    "M5": {
        "badge": "⚠️ M5: Assignment in Condition",
        "color": "#06b6d4",
        "message": (
            "Using `=` (assignment) inside an `if` condition may cause a `SyntaxError` "
            "or unintended behavior. Python requires `==` for equality checks."
        ),
        "hint": "Replace `=` with `==` in your `if` condition.",
    },
    "M6": {
        "badge": "⚠️ M6: Mutation vs New List",
        "color": "#8b5cf6",
        "message": (
            "Calling `.reverse()` modifies the **original list in-place**. "
            "Your function should return a new reversed list without changing the input."
        ),
        "hint": "Build a new list: `result = []` and append elements in reverse order.",
    },
    "M7": {
        "badge": "⚠️ M7: Index Boundary Confusion",
        "color": "#ec4899",
        "message": (
            "Using `range(len(nums) - 1, 0, -1)` stops before index 0, "
            "skipping the first element of the list."
        ),
        "hint": "Use `range(len(nums) - 1, -1, -1)` to include the element at index 0.",
    },
}


def get_intervention(misconception: str) -> Dict:
    """Return the intervention template for a given misconception code."""
    return INTERVENTION_TEMPLATES.get(misconception, INTERVENTION_TEMPLATES["M0"])


def build_memory_boxes(trace_frames: List[Dict]) -> List[Dict]:
    """
    Convert raw sys.settrace frames into simplified memory-box snapshots
    suitable for the frontend Visualizer component.

    Each memory box represents state at a specific source line,
    with only the 'interesting' variables (non-underscore, non-function).
    """
    boxes = []
    for i, frame in enumerate(trace_frames):
        if frame["event"] not in ("line", "return"):
            continue
        filtered_locals = {
            k: v for k, v in frame.get("locals", {}).items()
            if not k.startswith("_") and not callable(v)
        }
        boxes.append({
            "step": i,
            "event": frame["event"],
            "line": frame["line"],
            "source_line": frame.get("source_line", ""),
            "vars": filtered_locals,
        })
    return boxes
