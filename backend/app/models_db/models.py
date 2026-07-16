"""Database table definitions."""

from datetime import datetime, timezone
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import JSON
from sqlmodel import Field, Index, SQLModel


def utcnow() -> datetime:
    """Timezone-aware current UTC timestamp."""
    return datetime.now(timezone.utc)


class InspectionStatus(str, Enum):
    processing = "processing"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    modified = "modified"
    failed = "failed"


class HealthBand(str, Enum):
    healthy = "healthy"
    watch = "watch"
    at_risk = "at_risk"
    defect = "defect"
    unknown = "unknown"


class ModelType(str, Enum):
    image = "image"
    detection = "detection"
    tabular = "tabular"
    timeseries = "timeseries"
    audio = "audio"


class DecisionType(str, Enum):
    approve = "approve"
    reject = "reject"
    modify = "modify"


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class Inspection(SQLModel, table=True):
    __tablename__ = "inspection"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    product_ref: str | None = None
    machine_id: str | None = None
    category: str | None = None

    status: InspectionStatus = Field(default=InspectionStatus.processing)
    health_score: float | None = None
    health_band: HealthBand = Field(default=HealthBand.unknown)

    meta: dict = Field(default_factory=dict, sa_type=JSON)
    input_manifest: dict = Field(default_factory=dict, sa_type=JSON)

    # Populated by the language layer in later phases.
    llm_narrative: str | None = None
    llm_provider_used: str | None = None


class Prediction(SQLModel, table=True):
    __tablename__ = "prediction"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow)

    inspection_id: int = Field(foreign_key="inspection.id", index=True)
    model_type: ModelType
    model_version: str
    weights_sha256: str

    output: dict = Field(default_factory=dict, sa_type=JSON)
    confidence: float | None = None
    uncertainty: float | None = None
    raw_scores: dict = Field(default_factory=dict, sa_type=JSON)

    artifact_path: str | None = None
    input_sha256: str | None = None
    inference_ms: int | None = None


class HitlDecision(SQLModel, table=True):
    __tablename__ = "hitl_decision"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow)

    inspection_id: int = Field(foreign_key="inspection.id", index=True)
    decision: DecisionType
    reviewer: str = Field(default="inspector")
    corrected_label: str | None = None
    corrected_fields: dict = Field(default_factory=dict, sa_type=JSON)
    note: str | None = None
    feedback_path: str | None = None


class RetrainJob(SQLModel, table=True):
    __tablename__ = "retrain_job"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow)
    finished_at: datetime | None = None

    model_type: str = Field(index=True)
    status: JobStatus = Field(default=JobStatus.queued)
    progress: int = Field(default=0)

    base_version: str | None = None
    new_version: str | None = None
    num_corrections: int = 0
    num_samples: int = 0
    metrics: dict = Field(default_factory=dict, sa_type=JSON)
    message: str | None = None


class ModelVersion(SQLModel, table=True):
    __tablename__ = "model_version"
    # At most one active version per model_type, enforced at the database level.
    __table_args__ = (
        Index(
            "ix_model_version_active_unique",
            "model_type",
            unique=True,
            sqlite_where=sa.text("is_active = 1"),
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow)

    model_type: str = Field(index=True)
    version: str
    weights_path: str
    weights_sha256: str
    train_config: dict = Field(default_factory=dict, sa_type=JSON)
    metrics: dict = Field(default_factory=dict, sa_type=JSON)
    is_active: bool = Field(default=False)
    activated_at: datetime | None = None
