"""Detection inspection service: run YOLO, draw boxes, persist the inspection."""

from __future__ import annotations

import hashlib
import io
import time
from collections import Counter

from PIL import Image
from sqlmodel import Session

from app.config import get_settings
from app.models_db.models import Inspection, InspectionStatus, ModelType, Prediction
from app.schemas.inspect import Detection as DetectionDTO
from app.schemas.inspect import DetectionResult
from ml.detection.annotate import annotate
from ml.detection.infer import detect


def run_detection_inspection(
    session: Session,
    file_bytes: bytes,
    filename: str | None,
) -> DetectionResult:
    """Detect defects in an uploaded image, draw labeled boxes and persist the inspection."""
    input_sha = hashlib.sha256(file_bytes).hexdigest()
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")

    start = time.perf_counter()
    detections, bundle = detect(image)
    inference_ms = int((time.perf_counter() - start) * 1000)

    counts = dict(Counter(d.label for d in detections))
    top_confidence = max((d.confidence for d in detections), default=None)

    inspection = Inspection(
        product_ref=filename,
        category="detection",
        status=InspectionStatus.pending_review,
        meta={"filename": filename, "fallback_model": bundle.is_fallback},
    )
    session.add(inspection)
    session.commit()
    session.refresh(inspection)

    pred_row = Prediction(
        inspection_id=inspection.id,
        model_type=ModelType.detection,
        model_version=bundle.version,
        weights_sha256=bundle.weights_sha256 or "pretrained",
        output={
            "detections": [d.__dict__ for d in detections],
            "counts": counts,
            "n_defects": len(detections),
        },
        confidence=top_confidence,
        input_sha256=input_sha,
        inference_ms=inference_ms,
    )
    session.add(pred_row)
    session.commit()
    session.refresh(pred_row)

    overlay_path = get_settings().artifact_path / "detection" / f"{pred_row.id}.png"
    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    overlay_path.write_bytes(annotate(image, detections))
    pred_row.artifact_path = str(overlay_path)
    session.add(pred_row)
    session.commit()

    return DetectionResult(
        inspection_id=inspection.id,
        prediction_id=pred_row.id,
        detections=[DetectionDTO(label=d.label, confidence=d.confidence, box=d.box) for d in detections],
        counts=counts,
        n_defects=len(detections),
        annotated_url=f"/api/v1/explain/detection/{pred_row.id}",
        model_version=bundle.version,
        is_fallback=bundle.is_fallback,
        inference_ms=inference_ms,
    )
