"""
POST /api/reassess
Dual-gate fragile knowledge engine.
Evaluates a transfer solution + counter-probe trap and returns:
  - RESOLVED: passes both
  - SUPPRESSED: passes transfer but fails counter-probe (fragile knowledge)
  - UNRESOLVED: fails transfer
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Dict, List, Any

from backend.app.db import get_db
from backend.app.models import Learner, Problem, Reassessment, Diagnosis
from backend.app.core.sandbox import run_in_sandbox

router = APIRouter()


class ReassessRequest(BaseModel):
    learner_id: Optional[int] = None
    diagnosis_id: Optional[int] = None
    transfer_problem_id: Optional[int] = None
    counter_probe_problem_id: Optional[int] = None
    transfer_code: Optional[str] = ""
    counter_probe_code: Optional[str] = ""
    code: Optional[str] = None  # for Practice mode direct reassessment


class ReassessResponse(BaseModel):
    verdict: str           # "RESOLVED" | "SUPPRESSED" | "UNRESOLVED"
    transfer_passed: bool
    counter_probe_passed: bool
    badge: str
    message: str
    probabilities: Optional[Dict[str, float]] = None
    top_misconception: Optional[str] = None
    confidence: Optional[float] = None
    misconceptions: Optional[List[Dict]] = None


VERDICT_MESSAGES = {
    "RESOLVED": {
        "badge": "✅ RESOLVED: Conceptual Understanding Confirmed",
        "message": (
            "Excellent! Your updated solution resolves the misconception and passes verification."
        ),
    },
    "SUPPRESSED": {
        "badge": "⚠️ SUPPRESSED: Fragile Knowledge Detected",
        "message": (
            "You passed the transfer test but failed the counter-probe trap. "
            "This suggests your fix may be superficial — you've learned *what* works "
            "for this pattern but not *why*. Review the memory trace carefully."
        ),
    },
    "UNRESOLVED": {
        "badge": "❌ UNRESOLVED: Misconception Persists",
        "message": (
            "The misconception is still detected in your code. "
            "Re-read the intervention hint, examine highlighted lines, and try again."
        ),
    },
}


@router.post("/reassess", response_model=ReassessResponse)
def reassess(req: ReassessRequest, db: Session = Depends(get_db)):
    # 1. Practice Mode Direct Reassessment (when code is provided without transfer problem IDs)
    if req.code is not None and (not req.transfer_problem_id or not req.counter_probe_problem_id):
        from backend.app.core.sandbox import run_arbitrary_code
        from backend.app.core.features import extract_ast_features
        from backend.app.core.classifier import classify_arbitrary, get_top_misconception, localize_misconceptions

        exec_res = run_arbitrary_code(req.code)
        ast_feats = extract_ast_features(req.code)
        probs = classify_arbitrary(ast_feats, req.code, exec_res["status"])
        top_m, conf = get_top_misconception(probs)
        locs = localize_misconceptions(req.code, ast_feats, probs)

        resolved = (top_m == "M0" and not ast_feats.get("has_indentation_issue") and exec_res["status"] == "success")
        verdict = "RESOLVED" if resolved else "UNRESOLVED"
        v_data = VERDICT_MESSAGES[verdict]

        return ReassessResponse(
            verdict=verdict,
            transfer_passed=resolved,
            counter_probe_passed=resolved,
            badge=v_data["badge"],
            message=v_data["message"],
            probabilities=probs,
            top_misconception=top_m,
            confidence=conf,
            misconceptions=locs,
        )

    # 2. Problem Mode Dual-Gate Check
    transfer_problem = db.query(Problem).filter_by(id=req.transfer_problem_id).first() if req.transfer_problem_id else None
    counter_problem = db.query(Problem).filter_by(id=req.counter_probe_problem_id).first() if req.counter_probe_problem_id else None

    if not transfer_problem:
        raise HTTPException(status_code=404, detail="Transfer problem not found")
    if not counter_problem:
        raise HTTPException(status_code=404, detail="Counter-probe problem not found")

    # --- Gate 1: Transfer problem ---
    transfer_result = run_in_sandbox(req.transfer_code or "", transfer_problem.test_cases)
    transfer_passed = (transfer_result["passed"] == transfer_result["total"] and
                       transfer_result["total"] > 0 and
                       transfer_result["error"] is None)

    if not transfer_passed:
        verdict = "UNRESOLVED"
        v_data = VERDICT_MESSAGES[verdict]
        if req.learner_id:
            _persist(db, req, transfer_passed=False, counter_passed=False, verdict=verdict)
        return ReassessResponse(
            verdict=verdict,
            transfer_passed=False,
            counter_probe_passed=False,
            badge=v_data["badge"],
            message=v_data["message"],
        )

    # --- Gate 2: Counter-probe trap ---
    counter_result = run_in_sandbox(req.counter_probe_code, counter_problem.test_cases)
    counter_passed = (counter_result["passed"] == counter_result["total"] and
                      counter_result["total"] > 0 and
                      counter_result["error"] is None)

    verdict = "RESOLVED" if counter_passed else "SUPPRESSED"
    v_data = VERDICT_MESSAGES[verdict]

    _persist(db, req, transfer_passed=True, counter_passed=counter_passed, verdict=verdict)

    return ReassessResponse(
        verdict=verdict,
        transfer_passed=True,
        counter_probe_passed=counter_passed,
        badge=v_data["badge"],
        message=v_data["message"],
    )


def _persist(db, req, transfer_passed: bool, counter_passed: bool, verdict: str):
    ra = Reassessment(
        learner_id=req.learner_id,
        original_diagnosis_id=req.diagnosis_id,
        transfer_problem_id=req.transfer_problem_id,
        counter_probe_problem_id=req.counter_probe_problem_id,
        transfer_code=req.transfer_code,
        counter_probe_code=req.counter_probe_code,
        transfer_passed=transfer_passed,
        counter_probe_passed=counter_passed,
        verdict=verdict,
    )
    db.add(ra)
    db.commit()
