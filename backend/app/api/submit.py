"""
POST /api/submit
Runs learner code, computes execution signature + AST features,
returns diagnosis probabilities, probe requirement, and trace frames.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
import secrets

from backend.app.db import get_db
from backend.app.models import Learner, Problem, Submission, Diagnosis
from backend.app.core.sandbox import run_in_sandbox
from backend.app.core.features import extract_ast_features, generate_execution_signature
from backend.app.core.tracer import trace_code
from backend.app.core.classifier import classify, get_top_misconception, needs_probe
from backend.app.core.probe_bank import select_probe
from backend.app.core.interventions import get_intervention, build_memory_boxes

router = APIRouter()


class SubmitRequest(BaseModel):
    code: str
    problem_id: int
    session_token: Optional[str] = None


class SubmitResponse(BaseModel):
    submission_id: int
    passed: int
    total: int
    test_results: List[Dict]
    probabilities: Dict[str, float]
    top_misconception: str
    confidence: float
    probe_required: bool
    probe_id: Optional[str]
    probe: Optional[Dict]
    intervention: Dict
    memory_boxes: List[Dict]
    trace_frames: List[Dict]
    error: Optional[str]


@router.post("/submit", response_model=SubmitResponse)
def submit_code(req: SubmitRequest, db: Session = Depends(get_db)):
    # --- Fetch or create learner ---
    token = req.session_token or secrets.token_hex(16)
    learner = db.query(Learner).filter_by(session_token=token).first()
    if not learner:
        learner = Learner(name="anonymous", session_token=token)
        db.add(learner)
        db.flush()

    # --- Fetch problem ---
    problem = db.query(Problem).filter_by(id=req.problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    # --- Run sandbox ---
    sandbox_result = run_in_sandbox(req.code, problem.test_cases)

    # --- Extract features ---
    ast_feats = extract_ast_features(req.code)
    exec_sig = generate_execution_signature(req.code)

    # --- Trace (use first failing test input for visualization, or [1,2,3]) ---
    trace_input = [1, 2, 3]
    trace_frames = trace_code(req.code, trace_input)
    memory_boxes = build_memory_boxes(trace_frames)

    # --- Classify ---
    probs = classify(ast_feats, exec_sig, sandbox_result["passed"], sandbox_result["total"])
    top_m, confidence = get_top_misconception(probs)
    probe_required = needs_probe(probs)

    probe_id = None
    probe_data = None
    if probe_required:
        probe_id = select_probe(top_m, probs)
        if probe_id:
            from backend.app.core.probe_bank import get_probe_by_id
            probe_raw = get_probe_by_id(probe_id)
            if probe_raw:
                probe_data = {
                    "id": probe_raw["id"],
                    "question": probe_raw["question"],
                    "options": probe_raw["options"],
                }

    intervention = get_intervention(top_m)

    # --- Persist ---
    submission = Submission(
        learner_id=learner.id,
        problem_id=problem.id,
        code=req.code,
        passed_tests=sandbox_result["passed"],
        total_tests=sandbox_result["total"],
        execution_signature=exec_sig,
        ast_features=ast_feats,
        trace_frames=trace_frames[:50],  # store first 50 frames
    )
    db.add(submission)
    db.flush()

    diagnosis = Diagnosis(
        learner_id=learner.id,
        submission_id=submission.id,
        probabilities=probs,
        top_misconception=top_m,
        confidence=confidence,
        probe_required=probe_required,
        probe_question_id=probe_id,
    )
    db.add(diagnosis)
    db.commit()
    db.refresh(submission)
    db.refresh(diagnosis)

    return SubmitResponse(
        submission_id=submission.id,
        passed=sandbox_result["passed"],
        total=sandbox_result["total"],
        test_results=sandbox_result["results"],
        probabilities=probs,
        top_misconception=top_m,
        confidence=confidence,
        probe_required=probe_required,
        probe_id=probe_id,
        probe=probe_data,
        intervention=intervention,
        memory_boxes=memory_boxes,
        trace_frames=trace_frames[:50],
        error=sandbox_result["error"],
    )
