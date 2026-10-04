"""
Comprehensive Test Suite for Re:Learn System
Tests:
  - Database initialization & seeds
  - Feature extraction (AST + execution signatures)
  - Misconception classification (M0–M8)
  - Misconception localization
  - Visual explanations
  - Tracing & memory boxes
  - API endpoints: /api/submit, /api/practice, /api/probe/answer, /api/reassess, /api/inspector
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import init_db, SessionLocal
from backend.data.seed_data import seed
from backend.app.core.features import extract_ast_features, generate_execution_signature
from backend.app.core.classifier import classify, localize_misconceptions, build_visual_explanation
from backend.app.core.tracer import trace_code

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_db()
    seed()

# ---------------------------------------------------------------------------
# Core Engine Tests
# ---------------------------------------------------------------------------

def test_ast_feature_extraction_m1():
    code = (
        "def solution(nums):\n"
        "    for n in nums:\n"
        "        s = 0\n"
        "        s += n\n"
        "    return s\n"
    )
    feats = extract_ast_features(code)
    assert feats["accumulator_inside_loop"] is True
    assert feats["has_return"] is True

def test_ast_feature_extraction_m8_indentation():
    code = (
        "def solution(nums):\n"
        "    s = 0\n"
        "    for n in nums:\n"
        "    s += n\n"
        "    return s\n"
    )
    feats = extract_ast_features(code)
    assert feats["has_indentation_issue"] is True

def test_misconception_localization_m1():
    code = (
        "def solution(nums):\n"
        "    s = 0\n"
        "    for n in nums:\n"
        "        s = 0\n"
        "        s += n\n"
        "    return s\n"
    )
    feats = extract_ast_features(code)
    probs = {"M1": 0.8, "M0": 0.05}
    locs = localize_misconceptions(code, feats, probs)
    assert any(loc["type"] == "M1" for loc in locs)

def test_visual_explanation_generation():
    code = (
        "def solution(nums):\n"
        "    for n in nums:\n"
        "        s = 0\n"
        "        s += n\n"
        "    return s\n"
    )
    feats = extract_ast_features(code)
    probs = {"M1": 0.8, "M0": 0.05}
    locs = localize_misconceptions(code, feats, probs)
    expl = build_visual_explanation(code, locs, "M1")
    assert expl["type"] == "M1"
    assert len(expl["blocks"]) > 0

def test_tracer_memory_boxes():
    code = (
        "def solution(nums):\n"
        "    s = 0\n"
        "    for n in nums:\n"
        "        s += n\n"
        "    return s\n"
    )
    from backend.app.core.interventions import build_memory_boxes
    trace = trace_code(code, [1, 2, 3])
    assert len(trace) > 0
    assert any("s" in frame["locals"] for frame in trace)
    boxes = build_memory_boxes(trace)
    assert len(boxes) > 0
    assert any("s" in box["vars"] for box in boxes)

# ---------------------------------------------------------------------------
# API Endpoint Tests
# ---------------------------------------------------------------------------

def test_submit_correct_code():
    code = (
        "def solution(nums):\n"
        "    s = 0\n"
        "    for n in nums:\n"
        "        s += n\n"
        "    return s\n"
    )
    res = client.post("/api/submit", json={"code": code, "problem_id": 1})
    assert res.status_code == 200
    data = res.json()
    assert data["passed"] == data["total"]
    assert data["top_misconception"] == "M0"
    assert "visual_explanation" in data

def test_submit_m1_bug():
    code = (
        "def solution(nums):\n"
        "    for n in nums:\n"
        "        s = 0\n"
        "        s += n\n"
        "    return s\n"
    )
    res = client.post("/api/submit", json={"code": code, "problem_id": 1})
    assert res.status_code == 200
    data = res.json()
    assert data["top_misconception"] == "M1"
    assert len(data["misconceptions"]) > 0
    assert data["visual_explanation"] is not None

def test_practice_mode_endpoint():
    code = (
        "x = [1, 2, 3]\n"
        "total = 0\n"
        "for n in x:\n"
        "    total += n\n"
        "print('Result:', total)\n"
    )
    res = client.post("/api/practice", json={"code": code})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "Result: 6" in data["stdout"]
    assert len(data["memory_boxes"]) > 0

def test_practice_mode_syntax_error():
    code = (
        "def foo():\n"
        "return 42\n"
    )
    res = client.post("/api/practice", json={"code": code})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "syntax_error"
    assert data["top_misconception"] in ("M8", "M5")

def test_submit_m2_print_instead_of_return():
    code = (
        "def solution(nums):\n"
        "    s = 0\n"
        "    for n in nums:\n"
        "        s += n\n"
        "    print(s)\n"
    )
    res = client.post("/api/submit", json={"code": code, "problem_id": 1})
    assert res.status_code == 200
    data = res.json()
    assert data["top_misconception"] == "M2"

def test_submit_m3_off_by_one():
    code = (
        "def solution(nums):\n"
        "    s = 0\n"
        "    for i in range(len(nums) - 1):\n"
        "        s += nums[i]\n"
        "    return s\n"
    )
    res = client.post("/api/submit", json={"code": code, "problem_id": 1})
    assert res.status_code == 200
    data = res.json()
    assert data["top_misconception"] == "M3"

def test_submit_m4_wrong_comparison():
    code = (
        "def solution(nums):\n"
        "    m = nums[0]\n"
        "    for n in nums:\n"
        "        if n < m:\n"
        "            m = n\n"
        "    return m\n"
    )
    res = client.post("/api/submit", json={"code": code, "problem_id": 2})
    assert res.status_code == 200
    data = res.json()
    assert data["top_misconception"] == "M4"

def test_submit_m7_index_boundary():
    code = (
        "def solution(nums):\n"
        "    result = []\n"
        "    for i in range(len(nums) - 1, 0, -1):\n"
        "        result.append(nums[i])\n"
        "    return result\n"
    )
    res = client.post("/api/submit", json={"code": code, "problem_id": 3})
    assert res.status_code == 200
    data = res.json()
    assert data["top_misconception"] == "M7"

def test_probe_answer_flow():
    # Submit ambiguous/probe-triggering code
    code = (
        "def solution(nums):\n"
        "    for n in nums:\n"
        "        s = 0\n"
        "        s += n\n"
        "    return s\n"
    )
    res = client.post("/api/submit", json={"code": code, "problem_id": 1})
    data = res.json()
    sub_id = data["submission_id"]

    # Answer probe
    res_p = client.post("/api/probe/answer", json={
        "diagnosis_id": sub_id,
        "probe_id": "probe_m1_vs_m2",
        "selected_option": "A"
    })
    assert res_p.status_code == 200
    p_data = res_p.json()
    assert "updated_probabilities" in p_data
    assert "is_correct" in p_data

def test_dual_gate_reassessment():
    res = client.post("/api/reassess", json={
        "learner_id": 1,
        "diagnosis_id": 1,
        "transfer_problem_id": 1,
        "counter_probe_problem_id": 1,
        "transfer_code": "def solution(nums):\n    return sum(nums)\n",
        "counter_probe_code": "def solution(nums):\n    return sum(nums)\n",
    })
    assert res.status_code == 200
    data = res.json()
    assert "verdict" in data
    assert data["verdict"] in ("RESOLVED", "SUPERFICIAL_FIX", "UNRESOLVED")

def test_inspector_endpoints():
    res = client.get("/api/inspector")
    assert res.status_code == 200
    data = res.json()
    assert "confusion_matrix" in data
    assert "lopo_metrics" in data
    assert "overall_accuracy" in data

def test_inspector_problems():
    res = client.get("/api/inspector/problems")
    assert res.status_code == 200
    problems = res.json()
    assert len(problems) >= 3

def test_inspector_learners():
    res = client.get("/api/inspector/learners")
    assert res.status_code == 200
    learners = res.json()
    assert len(learners) > 0
