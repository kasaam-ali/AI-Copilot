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


class ShapContribution(BaseModel):
    feature: str
    value: float
    contribution: float


class TabularInspectionRequest(BaseModel):
    features: dict[str, float]


class TabularInspectionResult(BaseModel):
    inspection_id: int
    prediction_id: int
    label: str
    defect_probability: float
    confidence: float
    uncertainty: float
    base_value: float
    shap: list[ShapContribution]
    model_version: str
    weights_sha256: str
    inference_ms: int


class TabularSchema(BaseModel):
    features: list[str]
    defaults: dict[str, float]


class Detection(BaseModel):
    label: str
    confidence: float
    box: list[float]  # [x1, y1, x2, y2] in pixels


class DetectionResult(BaseModel):
    inspection_id: int
    prediction_id: int
    detections: list[Detection]
    counts: dict[str, int]
    n_defects: int
    annotated_url: str
    model_version: str
    is_fallback: bool
    inference_ms: int


class VideoDetectionResult(BaseModel):
    inspection_id: int
    prediction_id: int
    frames_sampled: int
    total_defects: int
    counts: dict[str, int]
    sample_frame_urls: list[str]
    model_version: str
    is_fallback: bool
    inference_ms: int


class TimeSeriesInspectionRequest(BaseModel):
    series: list[list[float]]


class SensorImportance(BaseModel):
    sensor: str
    importance: float
    magnitude: float


class TimeSeriesInspectionResult(BaseModel):
    inspection_id: int
    prediction_id: int
    label: str
    rul: float
    rul_cap: float
    risk: float
    confidence: float
    uncertainty: float
    sensors: list[str]
    sensor_importance: list[SensorImportance]
    model_version: str
    weights_sha256: str
    inference_ms: int


class HealthDriver(BaseModel):
    modality: str
    weight: float
    risk: float
    uncertainty: float
    contribution: float
    share: float


class SessionInspectionResult(BaseModel):
    inspection_id: int
    health_score: float | None
    health_band: str
    drivers: list[HealthDriver]
    image: ImageInspectionResult | None = None
    tabular: TabularInspectionResult | None = None
    timeseries: TimeSeriesInspectionResult | None = None
    errors: dict[str, str] = {}
