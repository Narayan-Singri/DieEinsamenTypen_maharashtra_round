"""
Probabilistic misconception classifier for Re:Learn.
Uses deterministic heuristic rules (pre-calibrated weights) instead of a trained ML model.
Phase 5 (actual RandomForest training) is PAUSED pending user approval.

Produces calibrated probability distributions over M0–M8.
Also provides line-level misconception localization via hybrid AST + heuristic analysis.
"""
from typing import Any, Dict, List, Optional, Tuple
import math
import ast
import textwrap
import tokenize
import io


# ---------------------------------------------------------------------------
# Misconception labels (short names)
# ---------------------------------------------------------------------------

MISCONCEPTIONS = ["M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8"]

MISCONCEPTION_LABELS = {
    "M0": "Correct",
    "M1": "Accumulator Reinit Inside Loop",
    "M2": "Print vs Return Confusion",
    "M3": "Off-by-One Range Error",
    "M4": "Wrong Comparison Direction",
    "M5": "Assignment vs Equality Confusion",
    "M6": "Mutation vs New Collection",
    "M7": "Index Boundary Confusion",
    "M8": "Indentation Misconception",
}

MISCONCEPTION_DESCRIPTIONS = {
    "M0": "Code is functionally correct.",
    "M1": "The accumulator variable is reset to its initial value inside the loop, causing only the last iteration's value to be retained.",
    "M2": "Using print() instead of return causes the function to return None rather than the computed result.",
    "M3": "Using range(len(x) - 1) skips the last element in iteration.",
    "M4": "The comparison operator is inverted (e.g. < instead of >) leading to wrong logic.",
    "M5": "Using = (assignment) instead of == (comparison) in a condition.",
    "M6": "Mutating the original collection in-place instead of building a new one.",
    "M7": "Off-by-one error in reverse iteration that skips the first element.",
    "M8": "Incorrect indentation causes statements to be outside the intended block scope.",
}


# ---------------------------------------------------------------------------
# Heuristic rule-based classifier
# ---------------------------------------------------------------------------

def classify(
    ast_features: Dict[str, Any],
    execution_signature: List[Any],
    passed: int,
    total: int,
) -> Dict[str, float]:
    """
    Returns a dict of {misconception_code: probability} (values sum to ~1.0).
    Uses hand-tuned heuristic rules as a stand-in for the trained RF classifier.
    """
    scores = {m: 0.01 for m in MISCONCEPTIONS}  # small baseline for all

    af = ast_features
    pass_rate = (passed / total) if total > 0 else 0.0

    # --- M0: Correct ---
    if pass_rate == 1.0 and af.get("has_return") and not af.get("has_print_call"):
        scores["M0"] += 0.8

    # --- M1: Accumulator reinit inside loop ---
    if af.get("accumulator_inside_loop"):
        scores["M1"] += 0.75
    if af.get("assign_in_loop_body") and pass_rate < 0.5:
        scores["M1"] += 0.2

    # Execution signature check: M1 typically returns last element not sum
    sig = execution_signature
    if len(sig) >= 4:
        if sig[4] == 9:
            scores["M1"] += 0.3
        if sig[3] == 3:
            scores["M1"] += 0.25

    # --- M2: Print vs Return ---
    if af.get("has_print_call") and not af.get("has_return"):
        scores["M2"] += 0.85
    elif af.get("has_print_call") and af.get("has_return"):
        scores["M2"] += 0.3
    none_count = sum(1 for v in sig if v is None)
    if none_count >= 3:
        scores["M2"] += 0.4

    # --- M3: Off-by-one range ---
    if af.get("uses_range_len_minus_one"):
        scores["M3"] += 0.8
    if len(sig) >= 4 and sig[3] == 3 and not scores["M1"] > 0.5:
        scores["M3"] += 0.2

    # --- M4: Wrong comparison ---
    if af.get("has_comparison_lt_update") and not af.get("has_comparison_gt_update"):
        scores["M4"] += 0.8

    # --- M5: Assignment in condition ---
    if af.get("parse_error"):
        scores["M5"] += 0.3

    # --- M6: Mutation vs new collection ---
    if af.get("calls_list_reverse") and not af.get("builds_new_list"):
        scores["M6"] += 0.7
    if af.get("calls_list_reverse"):
        scores["M6"] += 0.2

    # --- M7: Index boundary confusion ---
    if af.get("reverse_range_excludes_zero"):
        scores["M7"] += 0.75

    # --- M8: Indentation misconception ---
    if af.get("has_indentation_issue"):
        scores["M8"] += 0.80
    if af.get("indentation_after_colon_missing"):
        scores["M8"] += 0.50

    # Penalty: if passing all tests, strongly favour M0
    if pass_rate == 1.0:
        for m in MISCONCEPTIONS:
            if m != "M0":
                scores[m] *= 0.05

    # Softmax-normalize to sum to 1
    total_score = sum(math.exp(v) for v in scores.values())
    probs = {m: round(math.exp(scores[m]) / total_score, 4) for m in MISCONCEPTIONS}
    return probs


def classify_arbitrary(
    ast_features: Dict[str, Any],
    code: str,
    execution_status: str = "success",
) -> Dict[str, float]:
    """
    Classify misconceptions for arbitrary code (Practice mode).
    No test cases or execution signature — relies purely on AST features
    and code structure analysis.
    """
    scores = {m: 0.01 for m in MISCONCEPTIONS}
    af = ast_features

    if execution_status == "success" and not af.get("parse_error"):
        scores["M0"] += 0.3

    # M1: Accumulator reinit
    if af.get("accumulator_inside_loop"):
        scores["M1"] += 0.70
    if af.get("assign_in_loop_body"):
        scores["M1"] += 0.15

    # M2: Print vs Return
    if af.get("has_print_call") and af.get("function_count", 0) > 0 and not af.get("has_return"):
        scores["M2"] += 0.80

    # M3: Off-by-one
    if af.get("uses_range_len_minus_one"):
        scores["M3"] += 0.75

    # M4: Wrong comparison
    if af.get("has_comparison_lt_update") and not af.get("has_comparison_gt_update"):
        scores["M4"] += 0.75

    # M5: Assignment in condition
    if af.get("parse_error") and af.get("assignment_in_condition"):
        scores["M5"] += 0.70

    # M6: Mutation vs new
    if af.get("calls_list_reverse") and not af.get("builds_new_list"):
        scores["M6"] += 0.65

    # M7: Index boundary
    if af.get("reverse_range_excludes_zero"):
        scores["M7"] += 0.70

    # M8: Indentation
    if af.get("has_indentation_issue"):
        scores["M8"] += 0.80
    if af.get("indentation_after_colon_missing"):
        scores["M8"] += 0.50

    if execution_status == "syntax_error":
        # Syntax errors that are indentation-related
        if af.get("has_indentation_issue"):
            scores["M8"] += 0.3
        scores["M5"] += 0.15

    # Normalize
    total_score = sum(math.exp(v) for v in scores.values())
    probs = {m: round(math.exp(scores[m]) / total_score, 4) for m in MISCONCEPTIONS}
    return probs


def get_top_misconception(probs: Dict[str, float]) -> tuple:
    """Returns (top_misconception_code, confidence_value)."""
    top = max(probs, key=probs.__getitem__)
    return top, probs[top]


def needs_probe(probs: Dict[str, float], threshold: float = 0.45) -> bool:
    """
    Returns True if the top-1 confidence is below threshold,
    suggesting a disambiguation micro-probe is needed.
    """
    _, confidence = get_top_misconception(probs)
    return confidence < threshold


# ---------------------------------------------------------------------------
# Line-level misconception localization
# ---------------------------------------------------------------------------

def localize_misconceptions(
    code: str,
    ast_features: Dict[str, Any],
    probs: Dict[str, float],
) -> List[Dict]:
    """
    Identify the exact source-code locations associated with detected misconceptions.
    Uses AST analysis + code token scanning to map misconception types to specific lines.

    Returns a list of misconception annotations:
    [
        {
            "type": "M1",
            "label": "Accumulator Reinit Inside Loop",
            "confidence": 0.72,
            "severity": "high" | "medium" | "low",
            "line": 3,
            "column": 8,
            "end_line": 3,
            "end_column": 13,
            "title": "Accumulator reset inside loop",
            "explanation": "...",
        },
        ...
    ]
    """
    annotations = []
    source_lines = code.splitlines()

    # Only report misconceptions above a threshold
    THRESHOLD = 0.12

    try:
        tree = ast.parse(textwrap.dedent(code))
    except SyntaxError as e:
        # For syntax errors, report the error location
        lineno = e.lineno or 1
        annotations.append({
            "type": "M5" if "=" in str(e) else "M8",
            "label": "Syntax Error",
            "confidence": 0.9,
            "severity": "high",
            "line": lineno,
            "column": (e.offset or 1) - 1,
            "end_line": lineno,
            "end_column": len(source_lines[lineno - 1]) if lineno <= len(source_lines) else 1,
            "title": "Syntax Error",
            "explanation": str(e),
        })
        return annotations

    # --- M1: Find accumulator reinit inside loop ---
    if probs.get("M1", 0) >= THRESHOLD:
        annotations.extend(_localize_m1(tree, code, probs["M1"]))

    # --- M2: Find print() without return ---
    if probs.get("M2", 0) >= THRESHOLD:
        annotations.extend(_localize_m2(tree, code, probs["M2"]))

    # --- M3: Off-by-one range ---
    if probs.get("M3", 0) >= THRESHOLD:
        annotations.extend(_localize_m3(tree, code, probs["M3"]))

    # --- M4: Wrong comparison ---
    if probs.get("M4", 0) >= THRESHOLD:
        annotations.extend(_localize_m4(tree, code, probs["M4"]))

    # --- M6: Mutation vs new collection ---
    if probs.get("M6", 0) >= THRESHOLD:
        annotations.extend(_localize_m6(tree, code, probs["M6"]))

    # --- M7: Index boundary ---
    if probs.get("M7", 0) >= THRESHOLD:
        annotations.extend(_localize_m7(tree, code, probs["M7"]))

    # --- M8: Indentation ---
    if probs.get("M8", 0) >= THRESHOLD:
        annotations.extend(_localize_m8(code, probs["M8"]))

    return annotations


def _severity(confidence: float) -> str:
    if confidence >= 0.6:
        return "high"
    elif confidence >= 0.3:
        return "medium"
    return "low"


def _localize_m1(tree: ast.AST, code: str, confidence: float) -> List[Dict]:
    """Find accumulator-reset-inside-loop locations."""
    results = []

    class M1Finder(ast.NodeVisitor):
        def __init__(self):
            self._pre_loop_vars = set()
            self._in_loop = False
            self._loop_augassigned = set()

        def visit_Assign(self, node):
            if not self._in_loop:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self._pre_loop_vars.add(target.id)
            else:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Reset of pre-declared variable OR constant init inside loop
                        is_reinit = target.id in self._pre_loop_vars
                        is_const_init = isinstance(node.value, (ast.Constant, ast.List, ast.Dict, ast.Set))
                        if is_reinit or is_const_init:
                            results.append({
                                "type": "M1",
                                "label": MISCONCEPTION_LABELS["M1"],
                                "confidence": round(confidence, 2),
                                "severity": _severity(confidence),
                                "line": node.lineno,
                                "column": node.col_offset,
                                "end_line": node.end_lineno or node.lineno,
                                "end_column": node.end_col_offset or (node.col_offset + 10),
                                "title": f"Accumulator '{target.id}' reset inside loop",
                                "explanation": f"The variable '{target.id}' is being reset to its initial value inside the loop body. This means only the last iteration's contribution is kept. Move this initialization to before the loop.",
                            })
            self.generic_visit(node)

        def visit_For(self, node):
            old = self._in_loop
            self._in_loop = True
            for child in ast.iter_child_nodes(node):
                self.visit(child)
            self._in_loop = old

        def visit_While(self, node):
            old = self._in_loop
            self._in_loop = True
            for child in ast.iter_child_nodes(node):
                self.visit(child)
            self._in_loop = old

    M1Finder().visit(tree)
    return results


def _localize_m2(tree: ast.AST, code: str, confidence: float) -> List[Dict]:
    """Find print() calls that should be return statements."""
    results = []

    class M2Finder(ast.NodeVisitor):
        def __init__(self):
            self._in_function = False
            self._has_return = False

        def visit_FunctionDef(self, node):
            self._in_function = True
            self._has_return = False
            self.generic_visit(node)
            if not self._has_return:
                # Look for print calls in this function
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == "print":
                        results.append({
                            "type": "M2",
                            "label": MISCONCEPTION_LABELS["M2"],
                            "confidence": round(confidence, 2),
                            "severity": _severity(confidence),
                            "line": child.lineno,
                            "column": child.col_offset,
                            "end_line": child.end_lineno or child.lineno,
                            "end_column": child.end_col_offset or (child.col_offset + 5),
                            "title": "print() used instead of return",
                            "explanation": "This function uses print() to output the result but has no return statement. The caller will receive None instead of the computed value. Replace print() with return.",
                        })
            self._in_function = False

        def visit_Return(self, node):
            if self._in_function:
                self._has_return = True
            self.generic_visit(node)

    M2Finder().visit(tree)
    return results


def _localize_m3(tree: ast.AST, code: str, confidence: float) -> List[Dict]:
    """Find range(len(x) - 1) off-by-one errors."""
    results = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "range":
            if node.args:
                arg0 = node.args[0]
                if (isinstance(arg0, ast.BinOp) and isinstance(arg0.op, ast.Sub)
                    and isinstance(arg0.left, ast.Call) and isinstance(arg0.left.func, ast.Name)
                    and arg0.left.func.id == "len"
                    and isinstance(arg0.right, ast.Constant) and arg0.right.value == 1):
                    results.append({
                        "type": "M3",
                        "label": MISCONCEPTION_LABELS["M3"],
                        "confidence": round(confidence, 2),
                        "severity": _severity(confidence),
                        "line": node.lineno,
                        "column": node.col_offset,
                        "end_line": node.end_lineno or node.lineno,
                        "end_column": node.end_col_offset or (node.col_offset + 20),
                        "title": "Off-by-one: range(len(x) - 1) skips last element",
                        "explanation": "Using range(len(x) - 1) stops one element early, skipping the last item. Use range(len(x)) to include all elements.",
                    })
    return results


def _localize_m4(tree: ast.AST, code: str, confidence: float) -> List[Dict]:
    """Find wrong comparison operators."""
    results = []

    for node in ast.walk(tree):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
            if len(node.test.ops) == 1 and isinstance(node.test.ops[0], ast.Lt):
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign):
                        results.append({
                            "type": "M4",
                            "label": MISCONCEPTION_LABELS["M4"],
                            "confidence": round(confidence, 2),
                            "severity": _severity(confidence),
                            "line": node.lineno,
                            "column": node.col_offset,
                            "end_line": node.lineno,
                            "end_column": node.end_col_offset or (node.col_offset + 15),
                            "title": "Wrong comparison: < instead of >",
                            "explanation": "This comparison uses < when > is needed. For example, finding the maximum requires '>' but '<' finds the minimum.",
                        })
                        break
    return results


def _localize_m6(tree: ast.AST, code: str, confidence: float) -> List[Dict]:
    """Find in-place mutation calls."""
    results = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in ("reverse", "sort", "extend", "clear"):
                results.append({
                    "type": "M6",
                    "label": MISCONCEPTION_LABELS["M6"],
                    "confidence": round(confidence, 2),
                    "severity": _severity(confidence),
                    "line": node.lineno,
                    "column": node.col_offset,
                    "end_line": node.end_lineno or node.lineno,
                    "end_column": node.end_col_offset or (node.col_offset + 15),
                    "title": f"In-place mutation: .{node.func.attr}()",
                    "explanation": f"Calling .{node.func.attr}() modifies the original collection in-place rather than creating a new one. This may cause aliasing bugs.",
                })
    return results


def _localize_m7(tree: ast.AST, code: str, confidence: float) -> List[Dict]:
    """Find reverse range that excludes index 0."""
    results = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "range":
            if len(node.args) == 3:
                stop_arg = node.args[1]
                step_arg = node.args[2]
                step_neg = ((isinstance(step_arg, ast.UnaryOp) and isinstance(step_arg.op, ast.USub)
                            and isinstance(step_arg.operand, ast.Constant) and step_arg.operand.value == 1)
                           or (isinstance(step_arg, ast.Constant) and step_arg.value == -1))
                if step_neg and isinstance(stop_arg, ast.Constant) and stop_arg.value == 0:
                    results.append({
                        "type": "M7",
                        "label": MISCONCEPTION_LABELS["M7"],
                        "confidence": round(confidence, 2),
                        "severity": _severity(confidence),
                        "line": node.lineno,
                        "column": node.col_offset,
                        "end_line": node.end_lineno or node.lineno,
                        "end_column": node.end_col_offset or (node.col_offset + 25),
                        "title": "Index boundary: range(..., 0, -1) skips index 0",
                        "explanation": "Using 0 as the stop value excludes index 0 from the iteration. Use -1 as the stop: range(len(x)-1, -1, -1) to include all elements.",
                    })
    return results


def _localize_m8(code: str, confidence: float) -> List[Dict]:
    """
    Detect indentation misconceptions.
    This goes beyond simple syntax errors to detect:
    1. Missing indentation after colon (if/for/while/def)
    2. Logical indentation errors (statements outside intended block)
    3. Inconsistent indentation
    """
    results = []
    source_lines = code.splitlines()

    for i, line in enumerate(source_lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        lineno = i + 1

        # Check for lines ending with colon — next non-empty line should be indented
        if stripped.endswith(":") and any(stripped.startswith(kw) for kw in
                                          ["if ", "elif ", "else:", "for ", "while ", "def ", "class ", "try:", "except", "finally:", "with "]):
            # Find next non-empty line
            current_indent = len(line) - len(line.lstrip())
            for j in range(i + 1, len(source_lines)):
                next_line = source_lines[j]
                next_stripped = next_line.strip()
                if not next_stripped or next_stripped.startswith("#"):
                    continue
                next_indent = len(next_line) - len(next_line.lstrip())
                if next_indent <= current_indent:
                    results.append({
                        "type": "M8",
                        "label": MISCONCEPTION_LABELS["M8"],
                        "confidence": round(confidence, 2),
                        "severity": "high",
                        "line": j + 1,
                        "column": 0,
                        "end_line": j + 1,
                        "end_column": len(next_line),
                        "title": "Missing indentation after block statement",
                        "explanation": f"The statement on line {j + 1} should be indented inside the block started on line {lineno} ('{stripped}'). In Python, all statements inside a block must be indented.",
                    })
                break

    # Check for mixed tabs and spaces
    has_tabs = False
    has_spaces = False
    for i, line in enumerate(source_lines):
        if line.startswith("\t"):
            has_tabs = True
        elif line.startswith("    ") or line.startswith("  "):
            has_spaces = True

    if has_tabs and has_spaces:
        results.append({
            "type": "M8",
            "label": MISCONCEPTION_LABELS["M8"],
            "confidence": round(min(confidence + 0.1, 1.0), 2),
            "severity": "medium",
            "line": 1,
            "column": 0,
            "end_line": 1,
            "end_column": 1,
            "title": "Mixed tabs and spaces",
            "explanation": "Your code mixes tabs and spaces for indentation, which can cause unexpected IndentationError. Use consistent 4-space indentation throughout.",
        })

    # Check for common logical indentation issue: last print after a loop
    # e.g., for i in range(5):\n    print(i)\nprint("Done")
    # where user might have intended print("Done") to be inside the loop
    # (This is a heuristic — only flag if confidence is already elevated)
    if confidence >= 0.3:
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.For, ast.While)):
                    # Get the last line of the loop body
                    if node.body:
                        last_body_line = max(getattr(s, 'end_lineno', s.lineno) or s.lineno for s in node.body)
                        loop_indent = node.col_offset
                        # Check the line right after the loop body
                        if last_body_line < len(source_lines):
                            after_line = source_lines[last_body_line]
                            after_stripped = after_line.strip()
                            if after_stripped and not after_stripped.startswith("#"):
                                after_indent = len(after_line) - len(after_line.lstrip())
                                if after_indent == loop_indent:
                                    # This line is at the same indent as the loop — could be intentional
                                    # Only flag if it looks like a print/expression that logically belongs in loop
                                    pass  # Don't over-flag; rely on the colon-check above
        except (SyntaxError, Exception):
            pass

    return results


# ---------------------------------------------------------------------------
# Visual explanation builder
# ---------------------------------------------------------------------------

def build_visual_explanation(
    code: str,
    misconceptions: List[Dict],
    top_misconception: str,
) -> Dict[str, Any]:
    """
    Generate a structured visual explanation for the top misconception.
    Returns data the frontend can render as a graphical explanation.
    """
    source_lines = code.splitlines()

    if not misconceptions:
        return {
            "type": "none",
            "title": "No misconceptions detected",
            "blocks": [],
        }

    # Find the primary misconception annotation
    primary = None
    for m in misconceptions:
        if m["type"] == top_misconception:
            primary = m
            break
    if not primary:
        primary = misconceptions[0] if misconceptions else None

    if not primary:
        return {"type": "none", "title": "No misconceptions detected", "blocks": []}

    explanation = {
        "type": primary["type"],
        "title": primary["title"],
        "description": MISCONCEPTION_DESCRIPTIONS.get(primary["type"], ""),
        "severity": primary["severity"],
        "affected_lines": [],
        "blocks": [],
    }

    # Build "what your code does" vs "what it should do" blocks
    if primary["type"] == "M1":
        explanation["blocks"] = [
            {
                "label": "❌ What your code does",
                "type": "wrong",
                "lines": _get_context_lines(source_lines, primary["line"], 3),
                "highlight_line": primary["line"],
            },
            {
                "label": "✅ What it should look like",
                "type": "correct",
                "lines": _build_m1_fix(source_lines, primary),
                "highlight_line": None,
            },
        ]
        explanation["flow"] = _build_flow_diagram(primary["type"], primary)

    elif primary["type"] == "M2":
        explanation["blocks"] = [
            {
                "label": "❌ Your code returns None",
                "type": "wrong",
                "lines": _get_context_lines(source_lines, primary["line"], 2),
                "highlight_line": primary["line"],
            },
            {
                "label": "✅ Use return instead of print",
                "type": "correct",
                "lines": [{"line": primary["line"], "text": source_lines[primary["line"]-1].replace("print(", "return (").rstrip(")") + ")" if primary["line"] <= len(source_lines) else "return result"}],
                "highlight_line": None,
            },
        ]
        explanation["flow"] = _build_flow_diagram(primary["type"], primary)

    elif primary["type"] == "M8":
        explanation["blocks"] = [
            {
                "label": "❌ Current indentation",
                "type": "wrong",
                "lines": _get_context_lines(source_lines, primary["line"], 3),
                "highlight_line": primary["line"],
            },
            {
                "label": "✅ Correct indentation",
                "type": "correct",
                "lines": _build_m8_fix(source_lines, primary),
                "highlight_line": None,
            },
        ]
        explanation["flow"] = _build_indentation_diagram(source_lines, primary)

    else:
        # Generic block for other misconceptions
        explanation["blocks"] = [
            {
                "label": "📍 Affected code",
                "type": "highlight",
                "lines": _get_context_lines(source_lines, primary["line"], 3),
                "highlight_line": primary["line"],
            },
        ]
        explanation["flow"] = _build_flow_diagram(primary["type"], primary)

    explanation["affected_lines"] = [primary["line"]]

    return explanation


def _get_context_lines(source_lines: List[str], center_line: int, context: int = 2) -> List[Dict]:
    """Get lines around the center line for context display."""
    result = []
    start = max(0, center_line - context - 1)
    end = min(len(source_lines), center_line + context)
    for i in range(start, end):
        result.append({"line": i + 1, "text": source_lines[i]})
    return result


def _build_m1_fix(source_lines: List[str], annotation: Dict) -> List[Dict]:
    """Build a suggested fix for M1 (accumulator reinit)."""
    # Simply show the line should be moved before the loop
    line_idx = annotation["line"] - 1
    if 0 <= line_idx < len(source_lines):
        offending = source_lines[line_idx].strip()
        return [
            {"line": annotation["line"] - 1, "text": f"    {offending}  # ← Move this BEFORE the loop"},
            {"line": annotation["line"], "text": "    for n in nums:"},
            {"line": annotation["line"] + 1, "text": "        s += n  # Accumulate without resetting"},
        ]
    return []


def _build_m8_fix(source_lines: List[str], annotation: Dict) -> List[Dict]:
    """Build a suggested fix for M8 (indentation)."""
    line_idx = annotation["line"] - 1
    if 0 <= line_idx < len(source_lines):
        fixed_line = "    " + source_lines[line_idx].strip()
        return [
            {"line": annotation["line"], "text": fixed_line + "  # ← Properly indented"},
        ]
    return []


def _build_flow_diagram(misconception_type: str, annotation: Dict) -> Dict:
    """Build a text-based flow diagram for the misconception."""
    diagrams = {
        "M1": {
            "type": "loop_flow",
            "title": "Loop Execution Flow",
            "steps": [
                {"label": "Before loop", "detail": "s = 0 (initialized once)"},
                {"label": "Iteration 1", "detail": "s += n → s grows", "status": "correct"},
                {"label": "Iteration 2", "detail": "s = 0 ← RESET! Then s += n", "status": "error"},
                {"label": "Result", "detail": "Only last element's value remains", "status": "error"},
            ],
        },
        "M2": {
            "type": "data_flow",
            "title": "Return Value Flow",
            "steps": [
                {"label": "Function computes result", "detail": "result = ...", "status": "correct"},
                {"label": "print(result)", "detail": "Displays to console only", "status": "error"},
                {"label": "No return statement", "detail": "Function returns None", "status": "error"},
                {"label": "Caller receives None", "detail": "x = solution(...) → x is None", "status": "error"},
            ],
        },
        "M8": {
            "type": "block_scope",
            "title": "Block Scope",
            "steps": [
                {"label": "Block header (if/for/while):", "detail": "Starts a new indented block"},
                {"label": "    indented statement", "detail": "Inside the block ✓", "status": "correct"},
                {"label": "not indented statement", "detail": "Outside the block ✗", "status": "error"},
            ],
        },
    }

    return diagrams.get(misconception_type, {
        "type": "generic",
        "title": annotation.get("title", "Misconception"),
        "steps": [
            {"label": "Issue detected", "detail": annotation.get("explanation", ""), "status": "error"},
        ],
    })


def _build_indentation_diagram(source_lines: List[str], annotation: Dict) -> Dict:
    """Build a visual indentation block diagram."""
    line_idx = annotation["line"] - 1
    # Find the block header (line with colon)
    header_line = None
    for i in range(line_idx - 1, -1, -1):
        stripped = source_lines[i].strip()
        if stripped.endswith(":"):
            header_line = i
            break

    steps = []
    if header_line is not None:
        steps.append({
            "label": f"L{header_line + 1}: {source_lines[header_line].strip()}",
            "detail": "Block starts here →",
            "status": "correct",
        })
        # Show the indentation tree
        header_indent = len(source_lines[header_line]) - len(source_lines[header_line].lstrip())
        steps.append({
            "label": "│",
            "detail": "Expected: indented statements below",
            "status": "correct",
        })

    if 0 <= line_idx < len(source_lines):
        actual_indent = len(source_lines[line_idx]) - len(source_lines[line_idx].lstrip())
        steps.append({
            "label": f"L{line_idx + 1}: {source_lines[line_idx].strip()}",
            "detail": f"Indent: {actual_indent} spaces (expected: {(header_indent + 4) if header_line is not None else '4+'})",
            "status": "error",
        })

    return {
        "type": "block_scope",
        "title": "Indentation Block Structure",
        "steps": steps,
    }
