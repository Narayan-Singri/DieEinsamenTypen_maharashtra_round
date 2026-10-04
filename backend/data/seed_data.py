"""
Seed data for Re:Learn.
Populates the database with 5 base problems and pre-configured preset cases
covering the core misconception taxonomy (M0–M7).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from backend.app.db import SessionLocal, init_db
from backend.app.models import Problem, Learner
import secrets

# ---------------------------------------------------------------------------
# Problem definitions — 5 base problems targeting specific misconceptions
# ---------------------------------------------------------------------------

PROBLEMS = [
    {
        "slug": "sum_list",
        "title": "Sum a List of Numbers",
        "description": (
            "Write a function `solution(nums)` that returns the **sum** of all numbers "
            "in the list `nums`.\n\n"
            "**Example:**\n```\nsolution([1, 2, 3]) → 6\nsolution([4, 9]) → 13\n```"
        ),
        "starter_code": "def solution(nums):\n    # your code here\n    pass\n",
        "reference_solution": (
            "def solution(nums):\n"
            "    s = 0\n"
            "    for n in nums:\n"
            "        s += n\n"
            "    return s\n"
        ),
        "test_cases": [
            {"input": [], "expected_output": 0},
            {"input": [1], "expected_output": 1},
            {"input": [1, 2], "expected_output": 3},
            {"input": [1, 2, 3], "expected_output": 6},
            {"input": [4, 9], "expected_output": 13},
        ],
        "misconception_tags": ["M1", "M2", "M0"],
        "difficulty": "intro",
    },
    {
        "slug": "find_max",
        "title": "Find Maximum Value",
        "description": (
            "Write a function `solution(nums)` that returns the **maximum** value "
            "in the list.\n\n"
            "**Example:**\n```\nsolution([3, 1, 4]) → 4\nsolution([9]) → 9\n```"
        ),
        "starter_code": "def solution(nums):\n    # your code here\n    pass\n",
        "reference_solution": (
            "def solution(nums):\n"
            "    m = nums[0]\n"
            "    for n in nums:\n"
            "        if n > m:\n"
            "            m = n\n"
            "    return m\n"
        ),
        "test_cases": [
            {"input": [1], "expected_output": 1},
            {"input": [1, 2], "expected_output": 2},
            {"input": [3, 1, 4], "expected_output": 4},
            {"input": [4, 9], "expected_output": 9},
            {"input": [5, 3, 8, 1], "expected_output": 8},
        ],
        "misconception_tags": ["M3", "M4"],
        "difficulty": "intro",
    },
    {
        "slug": "count_even",
        "title": "Count Even Numbers",
        "description": (
            "Write a function `solution(nums)` that returns the **count** of even numbers "
            "in the list.\n\n"
            "**Example:**\n```\nsolution([1, 2, 3, 4]) → 2\nsolution([1, 3]) → 0\n```"
        ),
        "starter_code": "def solution(nums):\n    # your code here\n    pass\n",
        "reference_solution": (
            "def solution(nums):\n"
            "    count = 0\n"
            "    for n in nums:\n"
            "        if n % 2 == 0:\n"
            "            count += 1\n"
            "    return count\n"
        ),
        "test_cases": [
            {"input": [], "expected_output": 0},
            {"input": [1], "expected_output": 0},
            {"input": [2], "expected_output": 1},
            {"input": [1, 2, 3, 4], "expected_output": 2},
            {"input": [2, 4, 6], "expected_output": 3},
        ],
        "misconception_tags": ["M1", "M5"],
        "difficulty": "intro",
    },
    {
        "slug": "reverse_list",
        "title": "Reverse a List",
        "description": (
            "Write a function `solution(nums)` that returns a **new list** with the elements "
            "of `nums` in reverse order.\n\n"
            "**Example:**\n```\nsolution([1, 2, 3]) → [3, 2, 1]\n```"
        ),
        "starter_code": "def solution(nums):\n    # your code here\n    pass\n",
        "reference_solution": (
            "def solution(nums):\n"
            "    result = []\n"
            "    for i in range(len(nums) - 1, -1, -1):\n"
            "        result.append(nums[i])\n"
            "    return result\n"
        ),
        "test_cases": [
            {"input": [], "expected_output": []},
            {"input": [1], "expected_output": [1]},
            {"input": [1, 2], "expected_output": [2, 1]},
            {"input": [1, 2, 3], "expected_output": [3, 2, 1]},
            {"input": [4, 9, 2], "expected_output": [2, 9, 4]},
        ],
        "misconception_tags": ["M6", "M7"],
        "difficulty": "intro",
    },
    {
        "slug": "sum_transfer",
        "title": "Sum a List (Transfer Problem)",
        "description": (
            "Write a function `solution(values)` that returns the **sum** of all numbers "
            "in `values`. The parameter name has changed — demonstrate you understand the concept.\n\n"
            "**Example:**\n```\nsolution([2, 5]) → 7\n```"
        ),
        "starter_code": "def solution(values):\n    # your code here\n    pass\n",
        "reference_solution": (
            "def solution(values):\n"
            "    total = 0\n"
            "    for v in values:\n"
            "        total += v\n"
            "    return total\n"
        ),
        "test_cases": [
            {"input": [], "expected_output": 0},
            {"input": [2], "expected_output": 2},
            {"input": [2, 5], "expected_output": 7},
            {"input": [1, 2, 3], "expected_output": 6},
            {"input": [4, 9], "expected_output": 13},
        ],
        "misconception_tags": ["M1", "M2"],
        "difficulty": "intro",
    },
]


# ---------------------------------------------------------------------------
# Preset learner configurations (for judge demo / quick-switching)
# ---------------------------------------------------------------------------

PRESET_LEARNERS = [
    {
        "name": "M0 — Correct Solution",
        "session_token": "preset-m0-correct",
        "code": "def solution(nums):\n    total = 0\n    for n in nums:\n        total += n\n    return total\n",
    },
    {
        "name": "M1 — Accumulator Reinit Inside Loop",
        "session_token": "preset-m1-reinit",
        "code": "def solution(nums):\n    total = 0\n    for n in nums:\n        total = 0\n        total += n\n    return total\n",
    },
    {
        "name": "M2 — Print vs Return Confusion",
        "session_token": "preset-m2-print",
        "code": "def solution(nums):\n    total = 0\n    for n in nums:\n        total += n\n    print(total)\n",
    },
    {
        "name": "M3 — Off-by-One Range Error",
        "session_token": "preset-m3-obo",
        "code": "def solution(nums):\n    total = 0\n    for i in range(len(nums) - 1):\n        total += nums[i]\n    return total\n",
    },
    {
        "name": "M4 — Wrong Comparison Direction",
        "session_token": "preset-m4-comparator",
        "code": "def solution(nums):\n    m = nums[0]\n    for n in nums:\n        if n < m:\n            m = n\n    return m\n",
    },
    {
        "name": "M5 — Assignment vs Equality in Condition",
        "session_token": "preset-m5-assign",
        "code": "def solution(nums):\n    count = 0\n    for n in nums:\n        if n % 2 = 0:\n            count += 1\n    return count\n",
    },
    {
        "name": "M6 — Mutation vs New Collection",
        "session_token": "preset-m6-mutation",
        "code": "def solution(nums):\n    nums.reverse()\n    return nums\n",
    },
    {
        "name": "M7 — Index Boundary Confusion (Reverse)",
        "session_token": "preset-m7-index-boundary",
        "code": "def solution(nums):\n    result = []\n    for i in range(len(nums) - 1, 0, -1):\n        result.append(nums[i])\n    return result\n",
    },
    {
        "name": "M8 — Indentation & Scoping Inconsistency",
        "session_token": "preset-m8-indentation",
        "code": "num = 4\nif num % 2 == 0:\n    print('Even')\n\nelse:\n  print('Odd')\n",
    },
    {
        "name": "M9 — Parenthesis & Bracket Mismatch",
        "session_token": "preset-m9-brackets",
        "code": "def solution(nums):\n    total = sum(nums\n    return total\n",
    },
    {
        "name": "Fragile Knowledge (SUPPRESSED)",
        "session_token": "preset-fragile",
        "code": "def solution(nums):\n    # Hardcoded edge cases but missing general pattern\n    if nums == [1, 2, 3]: return 6\n    if nums == [4, 9]: return 13\n    return 0\n",
    },
]


def seed():
    """Run once to populate the database with problems and preset learners."""
    init_db()
    db = SessionLocal()
    try:
        # Seed problems
        for p_data in PROBLEMS:
            existing = db.query(Problem).filter_by(slug=p_data["slug"]).first()
            if not existing:
                prob = Problem(**p_data)
                db.add(prob)
                print(f"  [+] Problem: {p_data['title']}")

        # Seed or update preset learners
        for l_data in PRESET_LEARNERS:
            existing = db.query(Learner).filter_by(session_token=l_data["session_token"]).first()
            if not existing:
                learner = Learner(**l_data)
                db.add(learner)
                print(f"  [+] Preset learner: {l_data['name']}")
            else:
                existing.name = l_data["name"]
                existing.code = l_data.get("code")
                print(f"  [*] Updated preset learner: {l_data['name']}")

        db.commit()
        print("\n[OK] Seed complete.")
    except Exception as e:
        db.rollback()
        print(f"[ERR] Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("[SEED] Seeding Re:Learn database...")
    seed()
