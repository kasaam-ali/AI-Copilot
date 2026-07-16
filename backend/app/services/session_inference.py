"""Session inspection service: the multimodal hero endpoint.

Runs whichever modalities are supplied, persists them under ONE inspection, and fuses
their signals into a single Health Score. A single modality failing does not fail the
session: that modality is reported in ``errors`` and the fusion renormalizes over the rest.
"""

from __future__ import annotations

from loguru import logger
from sqlmodel import Session

from app.models_db.models import Inspection, InspectionStatus
from app.schemas.inspect import HealthDriver, SessionInspectionResult
from app.services.fusion import ModalitySignal, fuse
from app.services.image_inference import infer_and_persist_image
from app.services.tabular_inference import infer_and_persist_tabular
from app.services.timeseries_inference import infer_and_persist_timeseries


def run_session(
    session: Session,
    *,
    image_bytes: bytes | None = None,
    image_filename: str | None = None,
    tabular_features: dict | None = None,
    series: list[list[float]] | None = None,
) -> SessionInspectionResult:
    """Run all supplied modalities under one inspection and fuse into a Health Score."""
    if image_bytes is None and tabular_features is None and series is None:
        raise ValueError("Provide at least one modality (image, tabular or timeseries).")

    inspection = Inspection(
        category="session",
        product_ref=image_filename,
        status=InspectionStatus.processing,
        meta={},
    )
    session.add(inspection)
    session.commit()
    session.refresh(inspection)

    results: dict[str, object] = {"image": None, "tabular": None, "timeseries": None}
    signals: dict[str, ModalitySignal] = {}
    errors: dict[str, str] = {}

    if image_bytes is not None:
        try:
            results["image"], signals["image"] = infer_and_persist_image(
                session, inspection, image_bytes, image_filename
            )
        except Exception as exc:  # noqa: BLE001 - one modality must not sink the session
            logger.exception("Image modality failed in session {}", inspection.id)
            errors["image"] = str(exc)

    if tabular_features is not None:
        try:
            results["tabular"], signals["tabular"] = infer_and_persist_tabular(
                session, inspection, tabular_features
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Tabular modality failed in session {}", inspection.id)
            errors["tabular"] = str(exc)

    if series is not None:
        try:
            results["timeseries"], signals["timeseries"] = infer_and_persist_timeseries(
                session, inspection, series
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Time-series modality failed in session {}", inspection.id)
            errors["timeseries"] = str(exc)

    fusion = fuse(signals)

    inspection.health_score = fusion.health_score
    inspection.health_band = fusion.health_band
    inspection.status = (
        InspectionStatus.failed if not signals else InspectionStatus.pending_review
    )
    session.add(inspection)
    session.commit()

    return SessionInspectionResult(
        inspection_id=inspection.id,
        health_score=fusion.health_score,
        health_band=fusion.health_band.value,
        drivers=[
            HealthDriver(
                modality=d["modality"],
                weight=d["weight"],
                risk=d["risk"],
                uncertainty=d["uncertainty"],
                contribution=d["contribution"],
                share=d["share"],
            )
            for d in fusion.drivers
        ],
        image=results["image"],
        tabular=results["tabular"],
        timeseries=results["timeseries"],
        errors=errors,
    )
