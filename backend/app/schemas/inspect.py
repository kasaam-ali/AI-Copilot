"""Data-transfer objects for inspection endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class ImageInspectionResult(BaseModel):
    inspection_id: int
    prediction_id: int
    label: str
    label_index: int
    confidence: float
    uncertainty: float
    defect_probability: float
    class_probs: dict[str, float]
    model_version: str
    weights_sha256: str
    inference_ms: int
    gradcam_url: str
