"""
ml/generate_dataset.py
Synthetic code mutator generator for Re:Learn.
Generates training data by mutating correct solutions with M1–M7 bugs.
STATUS: PAUSED — DO NOT RUN until Phase 5 is approved.
"""
import json
import random
import os
from typing import List, Dict

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "dataset.json")

# Canonical correct solution
CORRECT_SOLUTION = (
    "def solution(nums):\n"
    "    s = 0\n"
    "    for n in nums:\n"
    "        s += n\n"
    "    return s\n"
)

# Mutant templates per misconception
MUTANTS = {
    "M0": [CORRECT_SOLUTION],
    "M1": [
        "def solution(nums):\n    for n in nums:\n        s = 0\n        s += n\n    return s\n",
        "def solution(nums):\n    for n in nums:\n        total = 0\n        total = total + n\n    return total\n",
    ],
    "M2": [
        "def solution(nums):\n    s = 0\n    for n in nums:\n        s += n\n    print(s)\n",
        "def solution(nums):\n    s = 0\n    for n in nums:\n        s += n\n    print(s)\n    return\n",
    ],
    "M3": [
        "def solution(nums):\n    s = 0\n    for i in range(len(nums) - 1):\n        s += nums[i]\n    return s\n",
    ],
    "M4": [
        "def solution(nums):\n    m = nums[0]\n    for n in nums:\n        if n < m:\n            m = n\n    return m\n",
    ],
    "M5": [
        "def solution(nums):\n    count = 0\n    for n in nums:\n        if n % 2 == 0:\n            count = count + 1\n    return count\n",  # M5 is hard to mutate syntactically
    ],
    "M6": [
        "def solution(nums):\n    nums.reverse()\n    return nums\n",
    ],
    "M7": [
        "def solution(nums):\n    result = []\n    for i in range(len(nums) - 1, 0, -1):\n        result.append(nums[i])\n    return result\n",
    ],
    "M8": [
        "def solution(nums):\n    s = 0\n    for n in nums:\ns += n\n    return s\n",
        "def solution(nums):\n    s = 0\nfor n in nums:\n    s += n\nreturn s\n",
        "def solution(nums):\n    s = 0\n    for n in nums:\n        if n > 0:\n        s += n\n    return s\n",
    ],
}


def generate_dataset(n_per_class: int = 50) -> List[Dict]:
    """Generate n_per_class samples per misconception class."""
    dataset = []
    for label, templates in MUTANTS.items():
        for _ in range(n_per_class):
            code = random.choice(templates)
            dataset.append({"code": code, "label": label})
    random.shuffle(dataset)
    return dataset


if __name__ == "__main__":
    print("[+] Phase 5 Resumed: Generating synthetic dataset...")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    data = generate_dataset(n_per_class=100)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[OK] Dataset written to {OUTPUT_PATH} ({len(data)} samples)")
