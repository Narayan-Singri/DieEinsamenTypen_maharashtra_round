"""
POST /api/probe/answer
Applies a Bayesian probability update based on learner's 1-click probe answer.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, Optional
from datetime import datetime

from backend.app.db import get_db
from backend.app.models import Diagnosis, ProbeEvent
from backend.app.core.probe_bank import bayesian_update, get_probe_by_id
from backend.app.core.classifier import get_top_misconception, MISCONCEPTION_LABELS
from backend.app.core.interventions import get_intervention

router = APIRouter()


class ProbeAnswerRequest(BaseModel):
    diagnosis_id: int
    probe_id: str
    selected_option: str   # "A", "B", or "C"
    learner_id: Optional[int] = None


class ProbeAnswerResponse(BaseModel):
    updated_probabilities: Dict[str, float]
    top_misconception: str
    top_label: str
    confidence: float
    is_correct: bool
    correct_option: str
    feedback: str
    intervention: Dict


@router.post("/probe/answer", response_model=ProbeAnswerResponse)
def answer_probe(req: ProbeAnswerRequest, db: Session = Depends(get_db)):
    # --- Fetch existing diagnosis ---
    diagnosis = db.query(Diagnosis).filter(
        (Diagnosis.id == req.diagnosis_id) | (Diagnosis.submission_id == req.diagnosis_id)
    ).first()
    if not diagnosis:
        raise HTTPException(status_code=404, detail="Diagnosis not found")

    # --- Fetch probe ---
    probe = get_probe_by_id(req.probe_id)
    if not probe:
        raise HTTPException(status_code=404, detail="Probe not found")

    correct_option = probe["correct_option"]
    is_correct = (req.selected_option == correct_option)

    # --- Bayesian update ---
    current_probs = diagnosis.probabilities
    updated_probs = bayesian_update(current_probs, req.probe_id, req.selected_option)

    top_m, confidence = get_top_misconception(updated_probs)
    label = MISCONCEPTION_LABELS.get(top_m, top_m)
    intervention = get_intervention(top_m)

    # Feedback message
    option_text = probe["options"].get(req.selected_option, "")
    if is_correct:
        feedback = f"✅ Correct! Option ({req.selected_option}) — {option_text}. This confirms the diagnosis."
    else:
        correct_text = probe["options"].get(correct_option, "")
        feedback = (
            f"The correct answer was ({correct_option}) — {correct_text}. "
            f"Your selection updates the diagnosis probabilities."
        )

    # --- Persist probe event ---
    event = ProbeEvent(
        learner_id=req.learner_id or diagnosis.learner_id,
        diagnosis_id=diagnosis.id,
        question_id=req.probe_id,
        selected_option=req.selected_option,
        correct_option=correct_option,
        updated_probabilities=updated_probs,
        is_correct=is_correct,
    )
    db.add(event)

    # Update diagnosis with refined probabilities
    diagnosis.probabilities = updated_probs
    diagnosis.top_misconception = top_m
    diagnosis.confidence = confidence
    db.commit()

    return ProbeAnswerResponse(
        updated_probabilities=updated_probs,
        top_misconception=top_m,
        top_label=label,
        confidence=confidence,
        is_correct=is_correct,
        correct_option=correct_option,
        feedback=feedback,
        intervention=intervention,
    )
