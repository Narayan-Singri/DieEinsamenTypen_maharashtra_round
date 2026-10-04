"""
POST /api/practice
Runs arbitrary Python code (Practice mode), performs misconception detection,
tracing, and inspection without requiring a predefined problem.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from backend.app.core.sandbox import run_arbitrary_code
from backend.app.core.features import extract_ast_features
from backend.app.core.tracer import trace_arbitrary, extract_inspector_data
from backend.app.core.classifier import (
    classify_arbitrary, get_top_misconception,
    localize_misconceptions, build_visual_explanation,
    MISCONCEPTION_LABELS,
)
from backend.app.core.interventions import get_intervention, build_memory_boxes

router = APIRouter()


class PracticeRequest(BaseModel):
    code: str


class PracticeResponse(BaseModel):
    success: bool
    status: str = "success"
    stdout: Optional[str] = ""
    result: Optional[Any] = None
    error: Optional[str] = None
    execution: Dict[str, Any]
    probabilities: Dict[str, float]
    top_misconception: str
    top_label: str
    confidence: float
    misconceptions: List[Dict] = []
    intervention: Dict
    trace: List[Dict] = []
    memory_boxes: List[Dict] = []
    inspector: Dict
    visual_explanation: Dict
    model_answer: Optional[Dict] = None


@router.post("/practice", response_model=PracticeResponse)
def practice_code(req: PracticeRequest):
    """
    Execute arbitrary Python code in Practice mode.
    Returns execution results, misconception analysis, trace, and inspector data.
    """
    code = req.code

    # --- Run in sandbox ---
    exec_result = run_arbitrary_code(code)

    # --- Extract AST features ---
    ast_feats = {}
    try:
        ast_feats = extract_ast_features(code)
    except Exception:
        ast_feats = {"parse_error": True}

    # --- Classify misconceptions ---
    probs = {}
    try:
        probs = classify_arbitrary(ast_feats, code, exec_result["status"])
    except Exception:
        probs = {"M0": 1.0}

    top_m, confidence = get_top_misconception(probs)

    # --- Localize misconceptions ---
    misconception_locations = []
    try:
        misconception_locations = localize_misconceptions(code, ast_feats, probs)
    except Exception:
        pass

    # --- Visual explanation ---
    visual_explanation = {}
    try:
        visual_explanation = build_visual_explanation(code, misconception_locations, top_m)
    except Exception:
        visual_explanation = {"type": "none", "title": "No visual explanation available", "blocks": []}

    # --- Intervention ---
    intervention = {}
    try:
        intervention = get_intervention(top_m)
    except Exception:
        intervention = {"badge": "", "message": "", "hint": None, "color": "#888"}

    # --- Trace ---
    trace_frames = []
    try:
        trace_frames = trace_arbitrary(code)
    except Exception:
        pass

    # Build memory boxes from trace frames
    memory_boxes = []
    try:
        memory_boxes = build_memory_boxes(trace_frames)
    except Exception:
        pass

    # --- Inspector ---
    inspector_data = {}
    try:
        inspector_data = extract_inspector_data(trace_frames)
    except Exception:
        inspector_data = {"variables": [], "total_steps": 0, "has_functions": False, "functions": []}

    # Add runtime namespace variables to inspector if trace didn't capture them
    if exec_result.get("namespace") and not inspector_data.get("variables"):
        variables = []
        for var_name, var_val in exec_result["namespace"].items():
            try:
                type_name = type(var_val).__name__
            except Exception:
                type_name = "unknown"
            try:
                display_val = repr(var_val)
                if len(display_val) > 200:
                    display_val = display_val[:200] + "..."
            except Exception:
                display_val = "<unprintable>"
            variables.append({
                "name": var_name,
                "type": type_name,
                "value": var_val,
                "display_value": display_val,
                "scope": "global",
                "first_seen_step": 0,
                "last_modified_step": 0,
            })
        inspector_data["variables"] = variables

    # --- Execution result ---
    execution = {
        "stdout": exec_result.get("stdout", ""),
        "stderr": exec_result.get("stderr", ""),
        "status": exec_result.get("status", "error"),
        "error": exec_result.get("error"),
        "error_line": exec_result.get("error_line"),
        "error_type": exec_result.get("error_type"),
    }

    return PracticeResponse(
        success=exec_result["status"] == "success",
        status=exec_result.get("status", "error"),
        stdout=exec_result.get("stdout", ""),
        result=exec_result.get("result"),
        error=exec_result.get("error"),
        execution=execution,
        probabilities=probs,
        top_misconception=top_m,
        top_label=MISCONCEPTION_LABELS.get(top_m, top_m),
        confidence=confidence,
        misconceptions=misconception_locations,
        intervention=intervention,
        trace=trace_frames[:50] if trace_frames else memory_boxes,
        memory_boxes=memory_boxes,
        inspector=inspector_data,
        visual_explanation=visual_explanation,
        model_answer=None,
    )
