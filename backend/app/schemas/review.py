"""Data-transfer objects for the human-in-the-loop review queue and feedback."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models_db.models import DecisionType


class PredictionSummary(BaseModel):
    prediction_id: int
    model_type: str
    model_version: str
    label: str | None
    confidence: float | None
    uncertainty: float | None
    output: dict
    gradcam_url: str | None = None
    inference_ms: int | None = None


class InspectionSummary(BaseModel):
    id: int
    created_at: datetime
    category: str | None
    status: str
    health_score: float | None
    health_band: str
    max_uncertainty: float | None
    label: str | None
    n_predictions: int


class DecisionSummary(BaseModel):
    id: int
    created_at: datetime
    decision: DecisionType
    reviewer: str
    corrected_label: str | None
    corrected_fields: dict
    note: str | None


class InspectionDetail(InspectionSummary):
    predictions: list[PredictionSummary]
    decisions: list[DecisionSummary]
    product_ref: str | None = None


class FeedbackRequest(BaseModel):
    inspection_id: int
    decision: DecisionType
    corrected_label: str | None = None
    corrected_fields: dict = {}
    note: str | None = None
    reviewer: str = "inspector"


class FeedbackResult(BaseModel):
    inspection_id: int
    decision_id: int
    status: str
    feedback_path: str | None = None
