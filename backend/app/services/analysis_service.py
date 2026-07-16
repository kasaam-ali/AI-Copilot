"""Grounded LLM root-cause analysis of an inspection.

Builds a structured evidence context from the persisted predictions, asks the LLM layer to
narrate it (with a deterministic offline fallback), and stores the narrative on the inspection.
"""

from __future__ import annotations

import json

from sqlmodel import Session, select

from app.models_db.models import Inspection, Prediction, utcnow
from app.schemas.llm import AnalyzeResult, LLMAttemptOut
from app.services.llm import get_llm_service
from app.services.llm.mock import mock_analysis
from app.services.llm.prompts import ANALYZE_SYSTEM, build_analyze_user, validate_analyze


def build_context(session: Session, inspection_id: int) -> dict | None:
    inspection = session.get(Inspection, inspection_id)
    if inspection is None:
        return None

    predictions = session.exec(
        select(Prediction).where(Prediction.inspection_id == inspection_id)
    ).all()

    modalities: dict = {}
    for pred in predictions:
        kind = pred.model_type.value
        if kind == "image":
            modalities["image"] = {
                "_name": "the vision model",
                "label": pred.output.get("label"),
                "defect_probability": pred.raw_scores.get("defect_probability", 0.0),
                "confidence": pred.confidence,
                "uncertainty": pred.uncertainty,
            }
        elif kind == "tabular":
            drivers = pred.raw_scores.get("shap", [])[:3]
            modalities["tabular"] = {
                "_name": "the process-data model",
                "label": pred.output.get("label"),
                "defect_probability": pred.output.get("defect_probability", 0.0),
                "top_drivers": [
                    {"feature": d["feature"], "contribution": round(d["contribution"], 4)}
                    for d in drivers
                ],
            }
        elif kind == "timeseries":
            modalities["timeseries"] = {
                "_name": "the machine-health model",
                "label": pred.output.get("label"),
                "rul": pred.raw_scores.get("rul", pred.output.get("rul", 0.0)),
                "risk": pred.output.get("risk", 0.0),
                "top_sensors": pred.raw_scores.get("sensor_importance", [])[:3],
            }

    return {
        "inspection_id": inspection.id,
        "health_score": inspection.health_score,
        "health_band": inspection.health_band.value,
        "modalities": modalities,
    }


def analyze_inspection(session: Session, inspection_id: int) -> AnalyzeResult:
    context = build_context(session, inspection_id)
    if context is None:
        raise ValueError(f"Inspection {inspection_id} not found.")

    result = get_llm_service().complete_json(
        system=ANALYZE_SYSTEM,
        user=build_analyze_user(context),
        validate=validate_analyze,
        fallback=lambda: mock_analysis(context),
    )

    inspection = session.get(Inspection, inspection_id)
    inspection.llm_narrative = json.dumps(result.data)
    inspection.llm_provider_used = result.provider_used
    inspection.updated_at = utcnow()
    session.add(inspection)
    session.commit()

    return AnalyzeResult(
        inspection_id=inspection_id,
        provider_used=result.provider_used,
        model=result.model,
        attempts=[LLMAttemptOut(**a.__dict__) for a in result.attempts],
        **result.data,
    )
