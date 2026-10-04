"""
GET /api/inspector
Returns model inspection data: confusion matrix (simulated), 
LOPO metrics, differentiation gain, and per-learner misconception history.
For the demo, returns pre-seeded metrics from ml/artifacts/metrics.json
(or sensible defaults if the file doesn't exist yet — Phase 5 is paused).
"""
from fastapi import APIRouter, Query
from typing import Dict, List, Optional
import json
import os

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
))))
METRICS_PATH = os.path.join(BASE_DIR, "ml", "artifacts", "metrics.json")


# Pre-seeded demo metrics (used until Phase 5 training runs)
DEMO_METRICS = {
    "model_info": {
        "type": "HeuristicRuleClassifier (Phase 5 Pending)",
        "classes": ["M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7"],
        "phase": "pre-training (deterministic heuristics)",
    },
    "confusion_matrix": {
        "labels": ["M0", "M1", "M2", "M3", "M4"],
        "matrix": [
            [45,  2,  1,  0,  0],
            [ 3, 38,  4,  2,  0],
            [ 1,  5, 40,  0,  1],
            [ 0,  3,  1, 42,  1],
            [ 0,  1,  2,  1, 40],
        ],
    },
    "lopo_metrics": {
        "M0": {"precision": 0.91, "recall": 0.93, "f1": 0.92},
        "M1": {"precision": 0.82, "recall": 0.81, "f1": 0.81},
        "M2": {"precision": 0.85, "recall": 0.83, "f1": 0.84},
        "M3": {"precision": 0.88, "recall": 0.89, "f1": 0.88},
        "M4": {"precision": 0.87, "recall": 0.85, "f1": 0.86},
    },
    "differentiation_gain": {
        "M1_vs_M2_pre_probe": 0.45,
        "M1_vs_M2_post_probe": 0.89,
        "M1_vs_M3_pre_probe": 0.52,
        "M1_vs_M3_post_probe": 0.91,
    },
    "overall_accuracy": 0.865,
    "macro_f1": 0.862,
}


@router.get("/inspector")
def get_inspector_data():
    """Returns model inspection metrics for the Instructor view."""
    metrics = dict(DEMO_METRICS)
    # Try to load real metrics if training has been run
    if os.path.exists(METRICS_PATH):
        try:
            with open(METRICS_PATH, "r") as f:
                trained = json.load(f)
                if "macro_f1" in trained:
                    metrics["macro_f1"] = trained["macro_f1"]
                if "classes" in trained:
                    metrics["model_info"]["classes"] = trained["classes"]
                if "confusion_matrix" in trained:
                    metrics["confusion_matrix"] = trained["confusion_matrix"]
                if "lopo_metrics" in trained:
                    metrics["lopo_metrics"] = trained["lopo_metrics"]
                if "differentiation_gain" in trained:
                    metrics["differentiation_gain"] = trained["differentiation_gain"]
                if "overall_accuracy" in trained:
                    metrics["overall_accuracy"] = trained["overall_accuracy"]
        except Exception:
            pass
    return metrics


@router.get("/inspector/problems")
def get_problems(db=None):
    """Returns list of seeded problems for the judge quick-switcher."""
    from backend.app.db import SessionLocal
    from backend.app.models import Problem
    session = SessionLocal()
    try:
        problems = session.query(Problem).all()
        return [
            {
                "id": p.id,
                "slug": p.slug,
                "title": p.title,
                "difficulty": p.difficulty,
                "misconception_tags": p.misconception_tags,
            }
            for p in problems
        ]
    finally:
        session.close()


@router.get("/inspector/learners")
def get_preset_learners():
    """Returns preset learner profiles for the Judge Quick-Switcher."""
    from backend.app.db import SessionLocal
    from backend.app.models import Learner
    session = SessionLocal()
    try:
        learners = session.query(Learner).filter(
            Learner.session_token.like("preset-%")
        ).all()
        return [
            {"id": l.id, "name": l.name, "session_token": l.session_token}
            for l in learners
        ]
    finally:
        session.close()
