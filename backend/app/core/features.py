"""
Feature extraction and static analysis engine for Re:Learn.
Provides:
  1. Detailed Indentation & Scoping Analysis (tokenize + AST + line-level whitespace)
  2. AST structural feature extraction (M0–M8)
  3. Execution signature generation (5 fixed inputs)
"""
import ast
import io
import textwrap
import tokenize
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Fixed input set for execution signatures
# ---------------------------------------------------------------------------

FIXED_INPUTS: List[Any] = [[], [1], [1, 2], [1, 2, 3], [4, 9]]


# ---------------------------------------------------------------------------
# Layer 1: Indentation & Scoping Static Analyzer
# ---------------------------------------------------------------------------

def analyze_source_indentation(code: str) -> Dict[str, Any]:
    """
    Exhaustive static analysis of source code indentation.
    Detects:
      - Token-level IndentationError / TabError
      - Mixed tabs and spaces in leading whitespace
      - Inconsistent block indentation widths (e.g. 4 spaces in if vs 2 spaces in else)
      - Missing indentation after colon (block openers)
      - Unexpected indentation on non-block lines
      - Unindented statements that logically belong inside a block

    Returns a dict containing:
      - has_indentation_issue: bool
      - issues: List[Dict] with exact line, column, end_line, end_column, title, explanation
      - dominant_indent_width: int (e.g., 4 or 2)
      - mixed_tabs_spaces: bool
      - indentation_after_colon_missing: bool
      - inconsistent_block_widths: bool
    """
    result = {
        "has_indentation_issue": False,
        "issues": [],
        "dominant_indent_width": 4,
        "mixed_tabs_spaces": False,
        "indentation_after_colon_missing": False,
        "inconsistent_block_widths": False,
        "syntax_indent_error": False,
    }

    if not code or not code.strip():
        return result

    raw_lines = code.splitlines()

    # 1. Tokenize check — catches Python IndentationError / TabError directly
    try:
        token_gen = tokenize.generate_tokens(io.StringIO(code).readline)
        tokens = list(token_gen)
    except (tokenize.TokenError, IndentationError) as e:
        result["has_indentation_issue"] = True
        result["syntax_indent_error"] = True
        line_no = getattr(e, "lineno", 1) or 1
        col_offset = getattr(e, "offset", 0) or 0
        err_msg = str(e)
        result["issues"].append({
            "line": line_no,
            "column": max(0, col_offset - 1),
            "end_line": line_no,
            "end_column": len(raw_lines[line_no - 1]) if 0 < line_no <= len(raw_lines) else 10,
            "issue_type": "syntax_indent_error",
            "severity": "high",
            "title": "Indentation Syntax Error",
            "explanation": f"Python syntax error in indentation: {err_msg}. Ensure all statements inside a block are indented consistently.",
        })

    # 2. Line-by-line whitespace analysis
    has_tabs = False
    has_spaces = False
    indent_widths = []
    line_indents = []  # List of (line_num, indent_len, indent_str, is_empty, stripped_text)

    for i, line in enumerate(raw_lines):
        line_num = i + 1
        stripped = line.strip()
        if not stripped:
            line_indents.append((line_num, 0, "", True, ""))
            continue

        leading_ws = line[:len(line) - len(line.lstrip())]
        if "\t" in leading_ws:
            has_tabs = True
        if " " in leading_ws:
            has_spaces = True

        # Check for mixed tabs and spaces on the exact same line
        if "\t" in leading_ws and " " in leading_ws:
            result["mixed_tabs_spaces"] = True
            result["has_indentation_issue"] = True
            result["issues"].append({
                "line": line_num,
                "column": 0,
                "end_line": line_num,
                "end_column": len(leading_ws),
                "issue_type": "mixed_tabs_spaces",
                "severity": "high",
                "title": "Mixed Tabs and Spaces",
                "explanation": f"Line {line_num} mixes both tab and space characters in its indentation. Configure your editor to use 4 spaces.",
            })

        indent_len = len(leading_ws.expandtabs(4))
        if indent_len > 0:
            indent_widths.append(indent_len)
        line_indents.append((line_num, indent_len, leading_ws, False, stripped))

    if has_tabs and has_spaces:
        result["mixed_tabs_spaces"] = True
        result["has_indentation_issue"] = True

    # 3. Block structure & block indentation consistency
    # Detect block starters: if, elif, else, for, while, def, class, try, except, finally, with
    BLOCK_KEYWORDS = ("if ", "if(", "elif ", "elif(", "else:", "for ", "while ",
                      "def ", "class ", "try:", "except", "finally:", "with ")

    block_body_indents = []  # List of (header_line, header_keyword, header_indent, body_line, body_indent, indent_step)

    for i, (l_num, l_indent, l_ws, is_empty, text) in enumerate(line_indents):
        if is_empty or text.startswith("#"):
            continue

        if text.endswith(":") and any(text.startswith(kw) for kw in BLOCK_KEYWORDS):
            # Found a block opener on line l_num. Look for the next non-empty line
            body_found = False
            for j in range(i + 1, len(line_indents)):
                b_num, b_indent, b_ws, b_empty, b_text = line_indents[j]
                if b_empty or b_text.startswith("#"):
                    continue

                body_found = True
                indent_step = b_indent - l_indent

                if b_indent <= l_indent:
                    # Missing indentation after colon!
                    result["indentation_after_colon_missing"] = True
                    result["has_indentation_issue"] = True
                    result["issues"].append({
                        "line": b_num,
                        "column": 0,
                        "end_line": b_num,
                        "end_column": len(raw_lines[b_num - 1]),
                        "issue_type": "missing_indent",
                        "severity": "high",
                        "title": "Missing Indentation After Block Header",
                        "explanation": f"Line {b_num} ('{b_text}') is not indented. In Python, all code blocks following '{text}' (line {l_num}) must be indented.",
                        "expected_indent": l_indent + 4,
                        "actual_indent": b_indent,
                    })
                else:
                    block_body_indents.append((l_num, text, l_indent, b_num, b_indent, indent_step))
                break

    # 4. Check for inconsistent block indent widths across sibling / nested blocks
    # e.g. 'if' block body uses 4-space step, but 'else' block body uses 2-space step!
    if len(block_body_indents) >= 2:
        steps = [b[5] for b in block_body_indents]
        distinct_steps = set(steps)
        if len(distinct_steps) > 1:
            result["inconsistent_block_widths"] = True
            result["has_indentation_issue"] = True
            # Find the baseline/majority step
            majority_step = max(distinct_steps, key=steps.count) if steps else 4
            for l_num, text, l_indent, b_num, b_indent, indent_step in block_body_indents:
                if indent_step != majority_step:
                    result["issues"].append({
                        "line": b_num,
                        "column": 0,
                        "end_line": b_num,
                        "end_column": len(raw_lines[b_num - 1]),
                        "issue_type": "inconsistent_block_indent",
                        "severity": "high",
                        "title": f"Inconsistent Block Indentation ({indent_step} spaces vs {majority_step} spaces)",
                        "explanation": (
                            f"Line {b_num} ('{raw_lines[b_num - 1].strip()}') is indented with {indent_step} spaces, "
                            f"while other blocks use {majority_step} spaces. "
                            f"Python PEP8 requires a uniform 4-space indentation standard."
                        ),
                        "expected_indent": l_indent + majority_step,
                        "actual_indent": b_indent,
                    })

    # 5. Check for unexpected indentation on lines outside any block
    for i, (l_num, l_indent, l_ws, is_empty, text) in enumerate(line_indents):
        if is_empty or text.startswith("#"):
            continue
        if i == 0 and l_indent > 0:
            result["has_indentation_issue"] = True
            result["issues"].append({
                "line": l_num,
                "column": 0,
                "end_line": l_num,
                "end_column": len(raw_lines[l_num - 1]),
                "issue_type": "unexpected_indent",
                "severity": "high",
                "title": "Unexpected Indentation on First Line",
                "explanation": f"Line {l_num} has leading indentation ({l_indent} spaces) but is at top-level. Remove leading spaces.",
                "expected_indent": 0,
                "actual_indent": l_indent,
            })

    return result


# ---------------------------------------------------------------------------
# Layer 2: AST Structural Feature Extractor
# ---------------------------------------------------------------------------

class ASTFeatureExtractor(ast.NodeVisitor):
    """
    Walks the AST of submitted code and extracts structural signals
    that correlate with known misconceptions M0–M8.
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
            "has_comparison_lt_update": False,   # if x < max: max = x  (bug when finding max)
            "has_comparison_gt_update": False,   # if x > max: max = x  (correct)

            # M5 signals: assignment in condition
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
        self._loop_assigns: List[str] = []
        self._pre_loop_assigns: List[str] = []

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


def check_unmatched_parentheses(code: str) -> Dict[str, Any]:
    """
    Static analyzer for parenthesis, bracket, and brace balance (M9).
    Scans characters ignoring strings and comments.
    Catches:
      - Unclosed opening brackets: '(', '[', '{'
      - Unexpected closing brackets: ')', ']', '}'
      - Mismatched bracket types: e.g. '(]' or '{)'
    """
    result = {
        "has_parenthesis_error": False,
        "issues": [],
    }
    if not code or not code.strip():
        return result

    raw_lines = code.splitlines()
    matching_map = {')': '(', ']': '[', '}': '{'}
    opening_chars = set(matching_map.values())
    closing_chars = set(matching_map.keys())

    stack = []  # List of (char, line_no, col_no)

    # 1. Direct character scanner that tracks string/comment state line by line
    in_triple_single = False
    in_triple_double = False

    for line_idx, line in enumerate(raw_lines):
        line_no = line_idx + 1
        in_single = False
        in_double = False
        escaped = False

        i = 0
        while i < len(line):
            ch = line[i]

            # Check triple quotes
            if not in_single and not in_double:
                if line[i:i+3] == "'''":
                    in_triple_single = not in_triple_single
                    i += 3
                    continue
                elif line[i:i+3] == '"""':
                    in_triple_double = not in_triple_double
                    i += 3
                    continue

            if in_triple_single or in_triple_double:
                i += 1
                continue

            if escaped:
                escaped = False
                i += 1
                continue

            if ch == '\\':
                escaped = True
                i += 1
                continue

            if ch == "'" and not in_double:
                in_single = not in_single
                i += 1
                continue
            elif ch == '"' and not in_single:
                in_double = not in_double
                i += 1
                continue

            if in_single or in_double:
                i += 1
                continue

            if ch == '#':
                # Rest of line is comment
                break

            if ch in opening_chars:
                stack.append((ch, line_no, i))
            elif ch in closing_chars:
                if not stack:
                    result["has_parenthesis_error"] = True
                    result["issues"].append({
                        "line": line_no,
                        "column": i,
                        "end_line": line_no,
                        "end_column": i + 1,
                        "issue_type": "unexpected_closing_bracket",
                        "severity": "high",
                        "title": f"Unmatched Closing Bracket '{ch}'",
                        "explanation": f"Found closing '{ch}' on line {line_no} with no matching opening bracket.",
                    })
                else:
                    last_open, o_line, o_col = stack.pop()
                    if matching_map[ch] != last_open:
                        result["has_parenthesis_error"] = True
                        result["issues"].append({
                            "line": line_no,
                            "column": i,
                            "end_line": line_no,
                            "end_column": i + 1,
                            "issue_type": "mismatched_bracket",
                            "severity": "high",
                            "title": f"Mismatched Bracket: '{last_open}' closed with '{ch}'",
                            "explanation": f"Opening bracket '{last_open}' on line {o_line} was closed with mismatched '{ch}' on line {line_no}.",
                        })
            i += 1

    # Remaining unclosed openings
    while stack:
        unclosed_char, u_line, u_col = stack.pop()
        result["has_parenthesis_error"] = True
        result["issues"].append({
            "line": u_line,
            "column": u_col,
            "end_line": u_line,
            "end_column": u_col + 1,
            "issue_type": "unclosed_opening_bracket",
            "severity": "high",
            "title": f"Unclosed Bracket '{unclosed_char}'",
            "explanation": f"Opening bracket '{unclosed_char}' on line {u_line} is never closed.",
        })

    # 2. SyntaxError parsing fallback to catch Python tokenizer/parser errors
    if not result["has_parenthesis_error"]:
        try:
            ast.parse(textwrap.dedent(code))
        except SyntaxError as e:
            err_msg = str(e).lower()
            if any(k in err_msg for k in ("parenthesis", "was never closed", "closing parenthesis", "unmatched", "unexpected eof in multi-line statement")):
                result["has_parenthesis_error"] = True
                line_no = e.lineno or 1
                col = e.offset or 0
                result["issues"].append({
                    "line": line_no,
                    "column": max(0, col - 1),
                    "end_line": line_no,
                    "end_column": len(raw_lines[line_no-1]) if 0 < line_no <= len(raw_lines) else 10,
                    "issue_type": "syntax_parenthesis_error",
                    "severity": "high",
                    "title": "Unclosed Parenthesis / Syntax Error",
                    "explanation": f"Python syntax error in parenthesis: {e.msg if hasattr(e, 'msg') else str(e)}.",
                })

    return result


def extract_ast_features(code: str) -> Dict[str, Any]:
    """
    Parse and walk the AST of submitted code, augmented with static indentation and bracket analysis.
    Returns a comprehensive dict of boolean/numeric features.
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
        "inconsistent_block_widths": False,
        "syntax_indent_error": False,
        "indentation_issues": [],
        # M9 — Parenthesis & Bracket Syntax Error
        "has_parenthesis_error": False,
        "parenthesis_issues": [],
    }

    # 1. Run static indentation analysis
    indent_analysis = analyze_source_indentation(code)
    features["has_indentation_issue"] = indent_analysis["has_indentation_issue"]
    features["indentation_after_colon_missing"] = indent_analysis["indentation_after_colon_missing"]
    features["mixed_tabs_spaces"] = indent_analysis["mixed_tabs_spaces"]
    features["inconsistent_block_widths"] = indent_analysis["inconsistent_block_widths"]
    features["syntax_indent_error"] = indent_analysis["syntax_indent_error"]
    features["indentation_issues"] = indent_analysis["issues"]

    # 2. Run static parenthesis/bracket analysis (M9)
    paren_analysis = check_unmatched_parentheses(code)
    features["has_parenthesis_error"] = paren_analysis["has_parenthesis_error"]
    features["parenthesis_issues"] = paren_analysis["issues"]

    # 3. Check for assignment in condition before AST parsing (catches if x = 5:)
    for line in code.splitlines():
        st = line.strip()
        if (st.startswith("if ") or st.startswith("elif ") or st.startswith("while ")) and "=" in st and "==" not in st and "<=" not in st and ">=" not in st and "!=" not in st:
            features["assignment_in_condition"] = True

    # 4. AST walk
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
            features["syntax_indent_error"] = True
        if any(k in err_msg for k in ("parenthesis", "was never closed", "closing parenthesis", "unmatched")):
            features["has_parenthesis_error"] = True
            if not features["parenthesis_issues"]:
                features["parenthesis_issues"].append({
                    "line": e.lineno or 1,
                    "column": max(0, (e.offset or 1) - 1),
                    "end_line": e.lineno or 1,
                    "end_column": (e.offset or 1) + 1,
                    "issue_type": "unclosed_parenthesis",
                    "severity": "high",
                    "title": "Unclosed Parenthesis / Syntax Error",
                    "explanation": f"Syntax error in parenthesis: {e.msg if hasattr(e, 'msg') else str(e)}.",
                })

    return features


# ---------------------------------------------------------------------------
# Layer 3: Execution Signature Generator
# ---------------------------------------------------------------------------

def generate_execution_signature(code: str, timeout: float = 2.0) -> List[Any]:
    """
    Run the learner's `solution` function on 5 fixed inputs and capture outputs.
    Returns a list of 5 values (or error strings) to form an execution signature.

    Fixed inputs: [], [1], [1, 2], [1, 2, 3], [4, 9]
    """
    signature = []

    try:
        tree = ast.parse(textwrap.dedent(code))
    except SyntaxError:
        return ["SYNTAX_ERROR"] * len(FIXED_INPUTS)

    safe_builtins = {
        "abs": abs, "all": all, "any": any, "bin": bin, "bool": bool,
        "chr": chr, "dict": dict, "divmod": divmod,
        "enumerate": enumerate, "filter": filter, "float": float,
        "format": format, "frozenset": frozenset, "getattr": getattr,
        "hasattr": hasattr, "hash": hash, "hex": hex, "id": id,
        "int": int, "isinstance": isinstance, "len": len, "list": list,
        "map": map, "max": max, "min": min, "next": next,
        "oct": oct, "ord": ord, "pow": pow,
        "print": print, "range": range, "repr": repr, "reversed": reversed,
        "round": round, "set": set, "sorted": sorted, "str": str,
        "sum": sum, "tuple": tuple, "type": type, "zip": zip,
        "True": True, "False": False, "None": None,
        "ValueError": ValueError, "TypeError": TypeError,
        "IndexError": IndexError, "KeyError": KeyError,
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
