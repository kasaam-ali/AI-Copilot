"""Tabular inspection service: run the ANN, compute SHAP, persist the inspection."""

from __future__ import annotations

import hashlib
import json
import time

from sqlmodel import Session

from app.models_db.models import Inspection, InspectionStatus, ModelType, Prediction
from app.schemas.inspect import ShapContribution, TabularInspectionResult, TabularSchema
from ml.tabular.explain import compute_shap
from ml.tabular.infer import load_active_bundle, predict_tabular


def get_tabular_schema() -> TabularSchema:
    """Return the feature list and default values for building the input form."""
    bundle = load_active_bundle()
    return TabularSchema(features=bundle.features, defaults=bundle.defaults)


def run_tabular_inspection(session: Session, features: dict) -> TabularInspectionResult:
    """Run defect-probability inference plus SHAP on a feature dict and persist it."""
    input_sha = hashlib.sha256(
        json.dumps(features, sort_keys=True).encode("utf-8")
    ).hexdigest()

    start = time.perf_counter()
    prediction, x_scaled, raw, bundle = predict_tabular(features)
    base_value, top_contributions, all_contributions = compute_shap(
        bundle.model, bundle.background, x_scaled, bundle.features, raw
    )
    inference_ms = int((time.perf_counter() - start) * 1000)

    inspection = Inspection(
        category="tabular",
        status=InspectionStatus.pending_review,
        meta={"features": features},
        input_manifest={"tabular": input_sha},
    )
    session.add(inspection)
    session.commit()
    session.refresh(inspection)

    pred_row = Prediction(
        inspection_id=inspection.id,
        model_type=ModelType.tabular,
        model_version=bundle.version,
        weights_sha256=bundle.weights_sha256,
        output={"label": prediction.label, "defect_probability": prediction.defect_probability},
        confidence=prediction.confidence,
        uncertainty=prediction.uncertainty,
        raw_scores={"base_value": base_value, "shap": all_contributions},
        input_sha256=input_sha,
        inference_ms=inference_ms,
    )
    session.add(pred_row)
    session.commit()
    session.refresh(pred_row)

    return TabularInspectionResult(
        inspection_id=inspection.id,
        prediction_id=pred_row.id,
        label=prediction.label,
        defect_probability=prediction.defect_probability,
        confidence=prediction.confidence,
        uncertainty=prediction.uncertainty,
        base_value=base_value,
        shap=[ShapContribution(**item) for item in top_contributions],
        model_version=bundle.version,
        weights_sha256=bundle.weights_sha256,
        inference_ms=inference_ms,
    )
