"""
ml/generate_dataset.py
Generates a balanced, diverse synthetic Python code dataset across all 9 misconception classes (M0–M8).
"""
import json
import random
import os
from typing import List, Dict

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "dataset.json")

# Rich mutant templates per misconception class (M0–M8) across different problem types
MUTANTS = {
    "M0": [
        "def solution(nums):\n    s = 0\n    for n in nums:\n        s += n\n    return s\n",
        "def solution(nums):\n    if not nums:\n        return 0\n    total = 0\n    for x in nums:\n        total += x\n    return total\n",
        "def solution(nums):\n    m = nums[0]\n    for n in nums:\n        if n > m:\n            m = n\n    return m\n",
        "def solution(nums):\n    res = []\n    for i in range(len(nums) - 1, -1, -1):\n        res.append(nums[i])\n    return res\n",
        "def solution(nums):\n    count = 0\n    for x in nums:\n        if x % 2 == 0:\n            count += 1\n    return count\n",
    ],
    "M1": [
        "def solution(nums):\n    for n in nums:\n        s = 0\n        s += n\n    return s\n",
        "def solution(nums):\n    for n in nums:\n        total = 0\n        total = total + n\n    return total\n",
        "def solution(nums):\n    res = 0\n    for x in nums:\n        res = 0\n        res += x * 2\n    return res\n",
        "def solution(nums):\n    for val in nums:\n        acc = 0\n        acc += val\n    return acc\n",
    ],
    "M2": [
        "def solution(nums):\n    s = 0\n    for n in nums:\n        s += n\n    print(s)\n",
        "def solution(nums):\n    s = 0\n    for n in nums:\n        s += n\n    print(s)\n    return\n",
        "def solution(nums):\n    total = sum(nums)\n    print('Total is:', total)\n",
        "def solution(nums):\n    m = max(nums) if nums else 0\n    print(m)\n",
    ],
    "M3": [
        "def solution(nums):\n    s = 0\n    for i in range(len(nums) - 1):\n        s += nums[i]\n    return s\n",
        "def solution(nums):\n    total = 0\n    for idx in range(len(nums) - 1):\n        total += nums[idx]\n    return total\n",
        "def solution(nums):\n    res = []\n    for i in range(len(nums) - 1):\n        res.append(nums[i] * 2)\n    return res\n",
    ],
    "M4": [
        "def solution(nums):\n    m = nums[0]\n    for n in nums:\n        if n < m:\n            m = n\n    return m\n",
        "def solution(nums):\n    best = nums[0]\n    for x in nums:\n        if x < best:\n            best = x\n    return best\n",
        "def solution(nums):\n    max_val = -999999\n    for val in nums:\n        if val < max_val:\n            max_val = val\n    return max_val\n",
    ],
    "M5": [
        "def solution(nums):\n    count = 0\n    for n in nums:\n        if n = 0:\n            count += 1\n    return count\n",
        "def solution(nums):\n    res = []\n    for x in nums:\n        if x % 2 = 0:\n            res.append(x)\n    return res\n",
        "def solution(nums):\n    if len(nums) = 0:\n        return 0\n    return sum(nums)\n",
    ],
    "M6": [
        "def solution(nums):\n    nums.reverse()\n    return nums\n",
        "def solution(nums):\n    nums.sort()\n    return nums\n",
        "def solution(nums):\n    result = nums\n    result.reverse()\n    return result\n",
    ],
    "M7": [
        "def solution(nums):\n    result = []\n    for i in range(len(nums) - 1, 0, -1):\n        result.append(nums[i])\n    return result\n",
        "def solution(nums):\n    rev = []\n    for idx in range(len(nums) - 1, 0, -1):\n        rev.append(nums[idx])\n    return rev\n",
        "def solution(nums):\n    s = 0\n    for i in range(len(nums) - 1, 0, -1):\n        s += nums[i]\n    return s\n",
    ],
    "M8": [
        "def solution(nums):\n    s = 0\n    for n in nums:\ns += n\n    return s\n",
        "def solution(nums):\n    s = 0\nfor n in nums:\n    s += n\nreturn s\n",
        "def solution(nums):\n    if len(nums) > 0:\n        print('Non-empty')\n    else:\n  print('Empty')\n",
        "def solution(nums):\n  total = 0\n    for x in nums:\n        total += x\n  return total\n",
        "def solution(nums):\n    s = 0\n    for n in nums:\n        if n > 0:\n        s += n\n    return s\n",
        "num = 4\nif num % 2 == 0:\n    print('Even')\nelse:\n  print('Odd')\n",
    ],
    "M9": [
        "def solution(nums):\n    s = sum(nums\n    return s\n",
        "def solution(nums):\n    return [1, 2, 3)\n",
        "def solution(nums):\n    print('Result:', (1 + 2\n",
        "def solution(nums):\n    total = sum((x for x in nums)\n    return total\n",
        "def solution(nums):\n    if (len(nums) > 0:\n        return nums[0]\n    return 0\n",
        "def solution(nums):\n    return {1: 'a', 2: 'b']\n",
    ],
}


def generate_dataset(n_per_class: int = 60) -> List[Dict]:
    """Generate n_per_class samples per misconception class."""
    dataset = []
    for label, templates in MUTANTS.items():
        for _ in range(n_per_class):
            code = random.choice(templates)
            dataset.append({"code": code, "label": label})
    random.shuffle(dataset)
    return dataset


if __name__ == "__main__":
    print("[+] Generating comprehensive M0–M8 synthetic dataset...")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    data = generate_dataset(n_per_class=100)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[OK] Dataset written to {OUTPUT_PATH} ({len(data)} samples across {len(MUTANTS)} classes)")
