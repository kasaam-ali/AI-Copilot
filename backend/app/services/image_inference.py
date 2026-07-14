"""Image inspection service: run the CNN, persist results, produce a Grad-CAM overlay."""

from __future__ import annotations

import hashlib
import io
import time

from PIL import Image
from sqlmodel import Session

from app.config import get_settings
from app.models_db.models import Inspection, InspectionStatus, ModelType, Prediction
from app.schemas.inspect import ImageInspectionResult
from ml.image.gradcam import compute_gradcam_overlay
from ml.image.infer import predict_image


def run_image_inspection(
    session: Session,
    file_bytes: bytes,
    filename: str | None,
) -> ImageInspectionResult:
    """Run defect inference on an uploaded image and persist the inspection."""
    input_sha = hashlib.sha256(file_bytes).hexdigest()
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")

    start = time.perf_counter()
    prediction, input_tensor, bundle = predict_image(image)
    inference_ms = int((time.perf_counter() - start) * 1000)

    inspection = Inspection(
        product_ref=filename,
        category="image",
        status=InspectionStatus.pending_review,
        meta={"filename": filename},
        input_manifest={"image": input_sha},
    )
    session.add(inspection)
    session.commit()
    session.refresh(inspection)

    pred_row = Prediction(
        inspection_id=inspection.id,
        model_type=ModelType.image,
        model_version=bundle.version,
        weights_sha256=bundle.weights_sha256,
        output={
            "label": prediction.label,
            "label_index": prediction.label_index,
            "class_probs": prediction.class_probs,
        },
        confidence=prediction.confidence,
        uncertainty=prediction.uncertainty,
        raw_scores={"defect_probability": prediction.defect_probability},
        input_sha256=input_sha,
        inference_ms=inference_ms,
    )
    session.add(pred_row)
    session.commit()
    session.refresh(pred_row)

    overlay_path = get_settings().artifact_path / "gradcam" / f"{pred_row.id}.png"
    compute_gradcam_overlay(bundle.model, input_tensor, image, prediction.label_index, overlay_path)
    pred_row.artifact_path = str(overlay_path)
    session.add(pred_row)
    session.commit()

    return ImageInspectionResult(
        inspection_id=inspection.id,
        prediction_id=pred_row.id,
        label=prediction.label,
        label_index=prediction.label_index,
        confidence=prediction.confidence,
        uncertainty=prediction.uncertainty,
        defect_probability=prediction.defect_probability,
        class_probs=prediction.class_probs,
        model_version=bundle.version,
        weights_sha256=bundle.weights_sha256,
        inference_ms=inference_ms,
        gradcam_url=f"/api/v1/explain/gradcam/{pred_row.id}",
    )
