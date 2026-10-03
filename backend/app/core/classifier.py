"""
Probabilistic misconception classifier for Re:Learn.
Uses deterministic heuristic rules (pre-calibrated weights) instead of a trained ML model.
Phase 5 (actual RandomForest training) is PAUSED pending user approval.

Produces calibrated probability distributions over M0–M7.
"""
from typing import Any, Dict, List, Optional
import math


# ---------------------------------------------------------------------------
# Misconception labels (short names)
# ---------------------------------------------------------------------------

MISCONCEPTIONS = ["M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7"]

MISCONCEPTION_LABELS = {
    "M0": "Correct",
    "M1": "Accumulator Reinit Inside Loop",
    "M2": "Print vs Return Confusion",
    "M3": "Off-by-One Range Error",
    "M4": "Wrong Comparison Direction",
    "M5": "Assignment vs Equality Confusion",
    "M6": "Mutation vs New Collection",
    "M7": "Index Boundary Confusion",
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
    # e.g. solution([1,2,3]) == 3 (reinit)
    sig = execution_signature
    if len(sig) >= 4:
        # [4] = sig for [4,9]: M1 returns 9, correct returns 13
        if sig[4] == 9:
            scores["M1"] += 0.3
        # [3] = sig for [1,2,3]: M1 returns 3, correct returns 6
        if sig[3] == 3:
            scores["M1"] += 0.25

    # --- M2: Print vs Return ---
    if af.get("has_print_call") and not af.get("has_return"):
        scores["M2"] += 0.85
    elif af.get("has_print_call") and af.get("has_return"):
        scores["M2"] += 0.3
    # If sig values are all None (function returns None)
    none_count = sum(1 for v in sig if v is None)
    if none_count >= 3:
        scores["M2"] += 0.4

    # --- M3: Off-by-one range ---
    if af.get("uses_range_len_minus_one"):
        scores["M3"] += 0.8
    # sig[3] for [1,2,3]: off-by-one sum = 3 (skips last), correct = 6
    if len(sig) >= 4 and sig[3] == 3 and not scores["M1"] > 0.5:
        scores["M3"] += 0.2

    # --- M4: Wrong comparison ---
    if af.get("has_comparison_lt_update") and not af.get("has_comparison_gt_update"):
        scores["M4"] += 0.8

    # --- M5: Assignment in condition (can't reliably detect with AST; small signal) ---
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

    # Penalty: if passing all tests, strongly favour M0
    if pass_rate == 1.0:
        for m in MISCONCEPTIONS:
            if m != "M0":
                scores[m] *= 0.05

    # Softmax-normalize to sum to 1
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
