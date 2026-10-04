"""
Feature extraction for Re:Learn.
Two main extractors:
  1. AST structural parser — identifies code-level misconception signals
  2. Execution signature generator — evaluates code on 5 fixed inputs
"""
import ast
import textwrap
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Fixed input set for execution signatures
# ---------------------------------------------------------------------------

FIXED_INPUTS: List[Any] = [[], [1], [1, 2], [1, 2, 3], [4, 9]]


# ---------------------------------------------------------------------------
# AST Feature Extractor
# ---------------------------------------------------------------------------

class ASTFeatureExtractor(ast.NodeVisitor):
    """
    Walks the AST of submitted code and extracts structural signals
    that correlate with known misconceptions M0–M7.
    """

    def __init__(self):
        self.features: Dict[str, Any] = {
            # M1 signals: accumulator reset inside loop
            "accumulator_inside_loop": False,
            "assign_in_loop_body": False,

            # M2 signals: print vs return
            "has_return": False,
            "has_print_call": False,
            "returns_none_explicitly": False,

            # M3 signals: off-by-one range
            "uses_range_len_minus_one": False,
            "uses_range_len": False,

            # M4 signals: wrong comparator direction
            "has_comparison_lt_update": False,   # if x < max: max = x  (bug)
            "has_comparison_gt_update": False,   # if x > max: max = x  (correct)

            # M5 signals: assignment in condition (can't detect easily via AST; flagged as False)
            "assignment_in_condition": False,

            # M6 signals: mutation vs new collection
            "calls_list_reverse": False,
            "builds_new_list": False,

            # M7 signals: index boundary in reverse range
            "reverse_range_excludes_zero": False,

            # General
            "function_count": 0,
            "loop_count": 0,
            "has_for_loop": False,
            "has_while_loop": False,
        }
        self._loop_depth = 0
        self._loop_assigns: List[str] = []     # names assigned inside loops
        self._pre_loop_assigns: List[str] = [] # names assigned before any loop

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.features["function_count"] += 1
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return):
        self.features["has_return"] = True
        if node.value is None:
            self.features["returns_none_explicitly"] = True
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Detect print()
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            self.features["has_print_call"] = True

        # Detect list.reverse() or reversed()
        if isinstance(node.func, ast.Attribute) and node.func.attr == "reverse":
            self.features["calls_list_reverse"] = True
        if isinstance(node.func, ast.Name) and node.func.id == "reversed":
            self.features["calls_list_reverse"] = True

        # Detect range(len(x) - 1) vs range(len(x))
        if isinstance(node.func, ast.Name) and node.func.id == "range":
            if len(node.args) == 1:
                arg0 = node.args[0]
                # range(len(x) - 1) -> M3 bug
                if (
                    isinstance(arg0, ast.BinOp)
                    and isinstance(arg0.op, ast.Sub)
                    and isinstance(arg0.left, ast.Call)
                    and isinstance(arg0.left.func, ast.Name)
                    and arg0.left.func.id == "len"
                    and isinstance(arg0.right, ast.Constant)
                    and arg0.right.value == 1
                ):
                    self.features["uses_range_len_minus_one"] = True

                # range(len(x)) -> standard iteration
                elif (
                    isinstance(arg0, ast.Call)
                    and isinstance(arg0.func, ast.Name)
                    and arg0.func.id == "len"
                ):
                    self.features["uses_range_len"] = True

            elif len(node.args) == 3:
                # range(len(x) - 1, -1, -1) — correct reverse
                # range(len(x) - 1, 0, -1) — excludes index 0 (M7)
                stop_arg = node.args[1]
                step_arg = node.args[2]
                step_is_neg = (
                    isinstance(step_arg, ast.UnaryOp)
                    and isinstance(step_arg.op, ast.USub)
                    and isinstance(step_arg.operand, ast.Constant)
                    and step_arg.operand.value == 1
                ) or (
                    isinstance(step_arg, ast.Constant)
                    and step_arg.value == -1
                )
                if step_is_neg:
                    # stop == 0  => range(..., 0, -1) => excludes index 0
                    if isinstance(stop_arg, ast.Constant) and stop_arg.value == 0:
                        self.features["reverse_range_excludes_zero"] = True

        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self.features["has_for_loop"] = True
        self.features["loop_count"] += 1
        self._loop_depth += 1
        self._scan_loop_assigns(node.body)
        self.generic_visit(node)
        self._loop_depth -= 1

    def visit_While(self, node: ast.While):
        self.features["has_while_loop"] = True
        self.features["loop_count"] += 1
        self._loop_depth += 1
        self._scan_loop_assigns(node.body)
        self.generic_visit(node)
        self._loop_depth -= 1

    def _scan_loop_assigns(self, body: list):
        """
        Check if any accumulator variable is initialized or reset inside the loop body.
        Covers both:
          1. Variables declared before loop and reset inside loop: s = 0; for ...: s = 0
          2. Variables initialized inside loop and accumulated: for ...: s = 0; s += n
        """
        loop_assigned_constants = set()
        loop_augassigned = set()

        for stmt in body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        self.features["assign_in_loop_body"] = True
                        if target.id in self._pre_loop_assigns:
                            self.features["accumulator_inside_loop"] = True
                        if isinstance(stmt.value, (ast.Constant, ast.List, ast.Dict, ast.Set)):
                            loop_assigned_constants.add(target.id)
            elif isinstance(stmt, ast.AugAssign):
                if isinstance(stmt.target, ast.Name):
                    loop_augassigned.add(stmt.target.id)

        # If a variable is initialized with a constant inside the loop and also augassigned
        if loop_assigned_constants & loop_augassigned:
            self.features["accumulator_inside_loop"] = True

    def visit_Assign(self, node: ast.Assign):
        if self._loop_depth == 0:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self._pre_loop_assigns.append(target.id)
        # Detect result = [] (new list creation)
        for target in node.targets:
            if isinstance(target, ast.Name):
                if isinstance(node.value, ast.List) and len(node.value.elts) == 0:
                    self.features["builds_new_list"] = True
        self.generic_visit(node)

    def visit_If(self, node: ast.If):
        """
        Check if body of If contains an update that looks like:
          if x > max: max = x   → correct
          if x < max: max = x   → bug (M4)
        """
        test = node.test
        if isinstance(test, ast.Compare) and len(test.ops) == 1:
            op = test.ops[0]
            body_stmts = node.body
            for stmt in body_stmts:
                if isinstance(stmt, ast.Assign):
                    if isinstance(op, ast.Lt):
                        self.features["has_comparison_lt_update"] = True
                    elif isinstance(op, ast.Gt):
                        self.features["has_comparison_gt_update"] = True
        self.generic_visit(node)


def extract_ast_features(code: str) -> Dict[str, Any]:
    """
    Parse and walk the AST of submitted code.
    Returns a flat dict of boolean/integer features.
    """
    features = {
        "accumulator_inside_loop": False,
        "assign_in_loop_body": False,
        "has_return": False,
        "has_print_call": False,
        "returns_none_explicitly": False,
        "uses_range_len_minus_one": False,
        "uses_range_len": False,
        "has_comparison_lt_update": False,
        "has_comparison_gt_update": False,
        "assignment_in_condition": False,
        "calls_list_reverse": False,
        "builds_new_list": False,
        "reverse_range_excludes_zero": False,
        "function_count": 0,
        "loop_count": 0,
        "has_for_loop": False,
        "has_while_loop": False,
        "parse_error": False,
        # M8 — Indentation features
        "has_indentation_issue": False,
        "indentation_after_colon_missing": False,
        "mixed_tabs_spaces": False,
    }
    try:
        tree = ast.parse(textwrap.dedent(code))
        extractor = ASTFeatureExtractor()
        extractor.visit(tree)
        features.update(extractor.features)
    except SyntaxError as e:
        features["parse_error"] = True
        err_msg = str(e).lower()
        if "indent" in err_msg or "unexpected indent" in err_msg or "expected an indented block" in err_msg:
            features["has_indentation_issue"] = True

    # Run indentation analysis (works even on unparsable code)
    indent_features = _detect_indentation_issues(code)
    features.update(indent_features)

    return features


def _detect_indentation_issues(code: str) -> Dict[str, Any]:
    """
    Detect indentation-related issues using line-by-line analysis.
    Works even when AST parsing fails.
    """
    result = {
        "has_indentation_issue": False,
        "indentation_after_colon_missing": False,
        "mixed_tabs_spaces": False,
    }

    lines = code.splitlines()
    has_tabs = False
    has_spaces = False

    for i, line in enumerate(lines):
        if not line.strip():
            continue

        # Check for mixed tabs/spaces
        leading = line[:len(line) - len(line.lstrip())]
        if "\t" in leading:
            has_tabs = True
        if "    " in leading or "  " in leading:
            has_spaces = True

        stripped = line.strip()

        # Check if line ends with colon (block opener)
        if stripped.endswith(":") and any(stripped.startswith(kw) for kw in
                                          ["if ", "elif ", "else:", "for ", "while ",
                                           "def ", "class ", "try:", "except", "finally:", "with "]):
            current_indent = len(line) - len(line.lstrip())
            # Check next non-blank line
            for j in range(i + 1, len(lines)):
                next_line = lines[j]
                next_stripped = next_line.strip()
                if not next_stripped or next_stripped.startswith("#"):
                    continue
                next_indent = len(next_line) - len(next_line.lstrip())
                if next_indent <= current_indent:
                    result["indentation_after_colon_missing"] = True
                    result["has_indentation_issue"] = True
                break

    if has_tabs and has_spaces:
        result["mixed_tabs_spaces"] = True
        result["has_indentation_issue"] = True

    return result


# ---------------------------------------------------------------------------
# Execution Signature Generator
# ---------------------------------------------------------------------------

def generate_execution_signature(code: str, timeout: float = 2.0) -> List[Any]:
    """
    Run the learner's `solution` function on 5 fixed inputs and capture outputs.
    Returns a list of 5 values (or error strings) to form an execution signature.

    Fixed inputs: [], [1], [1, 2], [1, 2, 3], [4, 9]
    """
    from backend.app.core.sandbox import run_in_sandbox

    # Use a lightweight synthetic test spec
    test_cases = [
        {"input": list(inp) if isinstance(inp, list) else inp, "expected_output": None}
        for inp in FIXED_INPUTS
    ]

    # We can't use run_in_sandbox's pass/fail directly since expected_output is None.
    # Instead, re-exec manually to capture actual return values.
    signature = []

    # Compile once
    try:
        tree = ast.parse(textwrap.dedent(code))
    except SyntaxError:
        return ["SYNTAX_ERROR"] * len(FIXED_INPUTS)

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

    import threading

    for inp in FIXED_INPUTS:
        holder: Dict[str, Any] = {"result": "TIMEOUT", "done": False}

        def _run(input_val=inp, h=holder):
            ns = {"__builtins__": safe_builtins}
            try:
                exec(compile(textwrap.dedent(code), "<sig>", "exec"), ns)
                fn = ns.get("solution")
                if fn is None:
                    h["result"] = "NO_FUNCTION"
                else:
                    arg = list(input_val) if isinstance(input_val, list) else input_val
                    h["result"] = fn(arg)
            except Exception as e:
                h["result"] = f"ERROR:{type(e).__name__}"
            finally:
                h["done"] = True

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=timeout)
        signature.append(holder["result"])

    return signature
