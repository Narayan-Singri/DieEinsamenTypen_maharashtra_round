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
from typing import Optional

from backend.app.db import get_db
from backend.app.models import Learner, Problem, Reassessment, Diagnosis
from backend.app.core.sandbox import run_in_sandbox

router = APIRouter()


class ReassessRequest(BaseModel):
    learner_id: int
    diagnosis_id: Optional[int] = None
    transfer_problem_id: int
    counter_probe_problem_id: int
    transfer_code: str
    counter_probe_code: str


class ReassessResponse(BaseModel):
    verdict: str           # "RESOLVED" | "SUPPRESSED" | "UNRESOLVED"
    transfer_passed: bool
    counter_probe_passed: bool
    badge: str
    message: str


VERDICT_MESSAGES = {
    "RESOLVED": {
        "badge": "✅ RESOLVED: Conceptual Understanding Confirmed",
        "message": (
            "Excellent! Your solution passes both the transfer problem and the "
            "counter-probe trap. This indicates genuine conceptual understanding."
        ),
    },
    "SUPPRESSED": {
        "badge": "⚠️ SUPPRESSED: Fragile Knowledge Detected",
        "message": (
            "You passed the transfer problem but failed the counter-probe trap. "
            "This suggests your fix may be superficial — you've learned *what* works "
            "for this pattern but not *why*. Review the memory trace carefully."
        ),
    },
    "UNRESOLVED": {
        "badge": "❌ UNRESOLVED: Misconception Persists",
        "message": (
            "Your transfer solution did not pass the test cases. "
            "The underlying misconception has not yet been resolved. "
            "Re-read the intervention hint and try again."
        ),
    },
}


@router.post("/reassess", response_model=ReassessResponse)
def reassess(req: ReassessRequest, db: Session = Depends(get_db)):
    # --- Fetch problems ---
    transfer_problem = db.query(Problem).filter_by(id=req.transfer_problem_id).first()
    counter_problem = db.query(Problem).filter_by(id=req.counter_probe_problem_id).first()

    if not transfer_problem:
        raise HTTPException(status_code=404, detail="Transfer problem not found")
    if not counter_problem:
        raise HTTPException(status_code=404, detail="Counter-probe problem not found")

    # --- Gate 1: Transfer problem ---
    transfer_result = run_in_sandbox(req.transfer_code, transfer_problem.test_cases)
    transfer_passed = (transfer_result["passed"] == transfer_result["total"] and
                       transfer_result["total"] > 0 and
                       transfer_result["error"] is None)

    if not transfer_passed:
        verdict = "UNRESOLVED"
        v_data = VERDICT_MESSAGES[verdict]
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
