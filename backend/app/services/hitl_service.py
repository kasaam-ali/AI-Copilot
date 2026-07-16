"""Human-in-the-loop service: review queue, inspection detail and feedback capture."""

from __future__ import annotations

import json
from collections import defaultdict

from sqlmodel import Session, select

from app.models_db.models import (
    DecisionType,
    HitlDecision,
    Inspection,
    InspectionStatus,
    Prediction,
    utcnow,
)
from app.schemas.review import (
    DecisionSummary,
    FeedbackRequest,
    FeedbackResult,
    InspectionDetail,
    InspectionSummary,
    PredictionSummary,
)
from ml.registry import REPO_ROOT

FEEDBACK_DIR = REPO_ROOT / "data" / "feedback"

_DECISION_STATUS = {
    DecisionType.approve: InspectionStatus.approved,
    DecisionType.reject: InspectionStatus.rejected,
    DecisionType.modify: InspectionStatus.modified,
}


def _max_uncertainty(predictions: list[Prediction]) -> float | None:
    values = [p.uncertainty for p in predictions if p.uncertainty is not None]
    return max(values) if values else None


def _summary(inspection: Inspection, predictions: list[Prediction]) -> InspectionSummary:
    label = predictions[0].output.get("label") if len(predictions) == 1 else None
    return InspectionSummary(
        id=inspection.id,
        created_at=inspection.created_at,
        category=inspection.category,
        status=inspection.status.value,
        health_score=inspection.health_score,
        health_band=inspection.health_band.value,
        max_uncertainty=_max_uncertainty(predictions),
        label=label,
        n_predictions=len(predictions),
    )


def list_inspections(
    session: Session,
    sort: str = "uncertainty",
    status: str | None = None,
    limit: int = 50,
) -> list[InspectionSummary]:
    """Return inspection summaries, uncertainty-first by default (review low-confidence)."""
    query = select(Inspection)
    if status:
        query = query.where(Inspection.status == status)
    inspections = session.exec(query).all()

    ids = [i.id for i in inspections]
    by_inspection: dict[int, list[Prediction]] = defaultdict(list)
    if ids:
        for pred in session.exec(select(Prediction).where(Prediction.inspection_id.in_(ids))).all():
            by_inspection[pred.inspection_id].append(pred)

    summaries = [_summary(i, by_inspection[i.id]) for i in inspections]
    if sort == "uncertainty":
        summaries.sort(key=lambda s: (s.max_uncertainty is None, -(s.max_uncertainty or 0.0)))
    else:
        summaries.sort(key=lambda s: s.created_at, reverse=True)
    return summaries[:limit]


def _prediction_summary(pred: Prediction) -> PredictionSummary:
    gradcam_url = (
        f"/api/v1/explain/gradcam/{pred.id}"
        if pred.model_type.value == "image" and pred.artifact_path
        else None
    )
    return PredictionSummary(
        prediction_id=pred.id,
        model_type=pred.model_type.value,
        model_version=pred.model_version,
        label=pred.output.get("label"),
        confidence=pred.confidence,
        uncertainty=pred.uncertainty,
        output=pred.output,
        gradcam_url=gradcam_url,
        inference_ms=pred.inference_ms,
    )


def get_inspection_detail(session: Session, inspection_id: int) -> InspectionDetail | None:
    inspection = session.get(Inspection, inspection_id)
    if inspection is None:
        return None

    predictions = session.exec(
        select(Prediction).where(Prediction.inspection_id == inspection_id)
    ).all()
    decisions = session.exec(
        select(HitlDecision).where(HitlDecision.inspection_id == inspection_id)
    ).all()

    summary = _summary(inspection, predictions)
    return InspectionDetail(
        **summary.model_dump(),
        product_ref=inspection.product_ref,
        predictions=[_prediction_summary(p) for p in predictions],
        decisions=[
            DecisionSummary(
                id=d.id,
                created_at=d.created_at,
                decision=d.decision,
                reviewer=d.reviewer,
                corrected_label=d.corrected_label,
                corrected_fields=d.corrected_fields,
                note=d.note,
            )
            for d in sorted(decisions, key=lambda d: d.created_at, reverse=True)
        ],
    )


def record_feedback(session: Session, request: FeedbackRequest) -> FeedbackResult:
    """Persist an inspector decision, update inspection status and store the corrected sample."""
    inspection = session.get(Inspection, request.inspection_id)
    if inspection is None:
        raise ValueError(f"Inspection {request.inspection_id} not found.")

    decision = HitlDecision(
        inspection_id=inspection.id,
        decision=request.decision,
        reviewer=request.reviewer,
        corrected_label=request.corrected_label,
        corrected_fields=request.corrected_fields,
        note=request.note,
    )
    session.add(decision)
    session.commit()
    session.refresh(decision)

    # Persist the corrected sample so the active-learning flywheel (Phase 6) can consume it.
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    feedback_path = FEEDBACK_DIR / f"inspection_{inspection.id}_decision_{decision.id}.json"
    feedback_path.write_text(
        json.dumps(
            {
                "inspection_id": inspection.id,
                "category": inspection.category,
                "decision": request.decision.value,
                "corrected_label": request.corrected_label,
                "corrected_fields": request.corrected_fields,
                "note": request.note,
                "input_manifest": inspection.input_manifest,
                "meta": inspection.meta,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    decision.feedback_path = str(feedback_path)
    inspection.status = _DECISION_STATUS[request.decision]
    inspection.updated_at = utcnow()
    session.add(decision)
    session.add(inspection)
    session.commit()

    return FeedbackResult(
        inspection_id=inspection.id,
        decision_id=decision.id,
        status=inspection.status.value,
        feedback_path=str(feedback_path),
    )
