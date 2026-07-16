"""DTOs for the active-learning retrain flow and model versioning."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models_db.models import JobStatus


class RetrainJobOut(BaseModel):
    id: int
    created_at: datetime
    finished_at: datetime | None
    model_type: str
    status: JobStatus
    progress: int
    base_version: str | None
    new_version: str | None
    num_corrections: int
    num_samples: int
    metrics: dict
    message: str | None


class ModelVersionOut(BaseModel):
    version: str
    created_at: str | None
    is_active: bool
    metrics: dict


class ModelVersionsOut(BaseModel):
    model_type: str
    active: str | None
    versions: list[ModelVersionOut]
