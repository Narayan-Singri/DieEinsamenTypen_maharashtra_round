"""
Minimal-click discriminating micro-probe bank for Re:Learn.
Each probe is a single 3-option multiple-choice question designed to
disambiguate confusable misconception pairs (e.g., M1 vs M2).

Bayesian update logic is also housed here.
"""
from typing import Dict, List, Optional
import math


# ---------------------------------------------------------------------------
# Probe definitions
# ---------------------------------------------------------------------------

PROBE_BANK: Dict[str, Dict] = {
    "probe_m1_vs_m2": {
        "id": "probe_m1_vs_m2",
        "question": (
            "Consider this code:\n\n"
            "```python\n"
            "def solution(nums):\n"
            "    for n in nums:\n"
            "        s = 0\n"
            "        s += n\n"
            "    return s\n"
            "```\n\n"
            "What does `solution([4, 9])` return?"
        ),
        "options": {
            "A": "9",
            "B": "4",
            "C": "13",
        },
        "correct_option": "A",
        "discriminates": ["M1", "M2"],
        "update_weights": {
            # (selected_option, target_class) -> likelihood multiplier
            "A": {"M1": 3.5, "M2": 0.3, "M0": 0.2},
            "B": {"M1": 1.5, "M2": 0.5, "M0": 0.1},
            "C": {"M1": 0.2, "M2": 0.3, "M0": 4.0},
        },
    },
    "probe_m1_vs_m3": {
        "id": "probe_m1_vs_m3",
        "question": (
            "Consider this code:\n\n"
            "```python\n"
            "def solution(nums):\n"
            "    s = 0\n"
            "    for i in range(len(nums) - 1):\n"
            "        s += nums[i]\n"
            "    return s\n"
            "```\n\n"
            "What does `solution([1, 2, 3])` return?"
        ),
        "options": {
            "A": "3",
            "B": "6",
            "C": "5",
        },
        "correct_option": "A",
        "discriminates": ["M1", "M3"],
        "update_weights": {
            "A": {"M3": 4.0, "M1": 0.5, "M0": 0.1},
            "B": {"M3": 0.1, "M1": 0.2, "M0": 5.0},
            "C": {"M3": 1.5, "M1": 2.0, "M0": 0.2},
        },
    },
    "probe_m2_standalone": {
        "id": "probe_m2_standalone",
        "question": (
            "A function uses `print(result)` instead of `return result` at the end. "
            "When you call `x = solution([4, 9])`, what is the value of `x`?"
        ),
        "options": {
            "A": "None",
            "B": "13",
            "C": "An error is raised",
        },
        "correct_option": "A",
        "discriminates": ["M2"],
        "update_weights": {
            "A": {"M2": 4.0, "M1": 0.2, "M0": 0.1},
            "B": {"M2": 0.1, "M1": 0.3, "M0": 3.0},
            "C": {"M2": 1.5, "M1": 1.0, "M0": 0.3},
        },
    },
    "probe_m4_standalone": {
        "id": "probe_m4_standalone",
        "question": (
            "Consider this code:\n\n"
            "```python\n"
            "def solution(nums):\n"
            "    m = nums[0]\n"
            "    for n in nums:\n"
            "        if n < m:\n"
            "            m = n\n"
            "    return m\n"
            "```\n\n"
            "What does `solution([3, 1, 4])` return?"
        ),
        "options": {
            "A": "1",
            "B": "4",
            "C": "3",
        },
        "correct_option": "A",
        "discriminates": ["M4"],
        "update_weights": {
            "A": {"M4": 4.0, "M0": 0.1, "M1": 0.2},
            "B": {"M4": 0.2, "M0": 4.0, "M1": 0.2},
            "C": {"M4": 1.5, "M0": 0.5, "M1": 1.0},
        },
    },
}


# ---------------------------------------------------------------------------
# Probe selection
# ---------------------------------------------------------------------------

def select_probe(top_misconception: str, probs: Dict[str, float]) -> Optional[str]:
    """
    Choose the most discriminating probe based on the current top misconception.
    Returns a probe_id or None if no suitable probe exists.
    """
    candidates = []
    for pid, probe in PROBE_BANK.items():
        if top_misconception in probe["discriminates"]:
            candidates.append(pid)

    if not candidates:
        # Generic fallback: pick probe that discriminates between top-2 classes
        sorted_m = sorted(probs, key=probs.__getitem__, reverse=True)
        top2 = set(sorted_m[:2])
        for pid, probe in PROBE_BANK.items():
            if top2.intersection(set(probe["discriminates"])):
                return pid
        return None

    return candidates[0]


# ---------------------------------------------------------------------------
# Bayesian update
# ---------------------------------------------------------------------------

def bayesian_update(
    probs: Dict[str, float],
    probe_id: str,
    selected_option: str,
) -> Dict[str, float]:
    """
    Apply a Bayesian likelihood update to the probability distribution
    based on which probe option the learner selected.

    Returns the updated (renormalized) probability distribution.
    """
    probe = PROBE_BANK.get(probe_id)
    if probe is None:
        return probs

    weights = probe["update_weights"].get(selected_option, {})
    updated = {}
    for m, p in probs.items():
        multiplier = weights.get(m, 1.0)
        updated[m] = p * multiplier

    # Renormalize
    total = sum(updated.values())
    if total == 0:
        return probs
    return {m: round(v / total, 4) for m, v in updated.items()}


def get_probe_by_id(probe_id: str) -> Optional[Dict]:
    return PROBE_BANK.get(probe_id)
