"""Time-series inspection service: run the LSTM, compute IG, persist the inspection."""

from __future__ import annotations

import hashlib
import json
import time

from sqlmodel import Session

from app.models_db.models import Inspection, InspectionStatus, ModelType, Prediction
from app.schemas.inspect import SensorImportance, TimeSeriesInspectionResult
from app.services.fusion import ModalitySignal
from ml.timeseries.explain import integrated_gradients, sensor_importance
from ml.timeseries.infer import predict_timeseries


def infer_and_persist_timeseries(
    session: Session,
    inspection: Inspection,
    series: list[list[float]],
) -> tuple[TimeSeriesInspectionResult, ModalitySignal]:
    """Run RUL inference plus Integrated Gradients and persist under the given inspection."""
    input_sha = hashlib.sha256(
        json.dumps(series, sort_keys=True).encode("utf-8")
    ).hexdigest()

    start = time.perf_counter()
    prediction, window, bundle = predict_timeseries(series)
    attributions = integrated_gradients(bundle.model, window)
    top_sensors = sensor_importance(attributions, bundle.sensors)
    inference_ms = int((time.perf_counter() - start) * 1000)

    pred_row = Prediction(
        inspection_id=inspection.id,
        model_type=ModelType.timeseries,
        model_version=bundle.version,
        weights_sha256=bundle.weights_sha256,
        output={"label": prediction.label, "rul": prediction.rul, "risk": prediction.risk},
        confidence=prediction.confidence,
        uncertainty=prediction.uncertainty,
        raw_scores={
            "rul": prediction.rul,
            "rul_std": prediction.rul_std,
            "sensors": bundle.sensors,
            "attributions": attributions.tolist(),
            "sensor_importance": top_sensors,
        },
        input_sha256=input_sha,
        inference_ms=inference_ms,
    )
    session.add(pred_row)
    inspection.input_manifest = {**inspection.input_manifest, "timeseries": input_sha}
    session.add(inspection)
    session.commit()
    session.refresh(pred_row)

    result = TimeSeriesInspectionResult(
        inspection_id=inspection.id,
        prediction_id=pred_row.id,
        label=prediction.label,
        rul=prediction.rul,
        rul_cap=bundle.rul_cap,
        risk=prediction.risk,
        confidence=prediction.confidence,
        uncertainty=prediction.uncertainty,
        sensors=bundle.sensors,
        sensor_importance=[SensorImportance(**item) for item in top_sensors],
        model_version=bundle.version,
        weights_sha256=bundle.weights_sha256,
        inference_ms=inference_ms,
    )
    signal = ModalitySignal(risk=prediction.risk, uncertainty=prediction.uncertainty)
    return result, signal


def run_timeseries_inspection(
    session: Session, series: list[list[float]]
) -> TimeSeriesInspectionResult:
    """Run RUL inference plus IG as a standalone inspection."""
    inspection = Inspection(
        category="timeseries",
        status=InspectionStatus.pending_review,
        meta={"timesteps": len(series)},
    )
    session.add(inspection)
    session.commit()
    session.refresh(inspection)

    result, _ = infer_and_persist_timeseries(session, inspection, series)
    return result
