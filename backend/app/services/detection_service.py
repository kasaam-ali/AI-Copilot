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
from app.schemas.inspect import DetectionResult, FrameDetectionResult, VideoDetectionResult
from ml.detection.annotate import annotate
from ml.detection.infer import detect

MAX_VIDEO_FRAMES = 24
VIDEO_SAMPLE_FRAMES = 4


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


def run_frame_detection(file_bytes: bytes) -> FrameDetectionResult:
    """Detect on a single live-camera frame. Stateless and fast; nothing is persisted."""
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    start = time.perf_counter()
    detections, bundle = detect(image)
    inference_ms = int((time.perf_counter() - start) * 1000)
    return FrameDetectionResult(
        detections=[DetectionDTO(label=d.label, confidence=d.confidence, box=d.box) for d in detections],
        width=image.width,
        height=image.height,
        model_version=bundle.version,
        is_fallback=bundle.is_fallback,
        inference_ms=inference_ms,
    )


def run_video_detection(
    session: Session,
    file_bytes: bytes,
    filename: str | None,
) -> VideoDetectionResult:
    """Sample frames from a video, detect defects in each, and aggregate counts."""
    import tempfile
    from collections import Counter
    from pathlib import Path

    import cv2

    suffix = Path(filename or "clip.mp4").suffix or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    counts: Counter = Counter()
    total_defects = 0
    samples: list[tuple[int, bytes]] = []
    frames_sampled = 0
    bundle = None

    start = time.perf_counter()
    try:
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            raise ValueError("Could not read the video file.")
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        step = max(1, total // MAX_VIDEO_FRAMES) if total else 1

        index = 0
        while frames_sampled < MAX_VIDEO_FRAMES:
            ok, frame = cap.read()
            if not ok:
                break
            if index % step == 0:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil = Image.fromarray(rgb)
                detections, bundle = detect(pil)
                counts.update(d.label for d in detections)
                total_defects += len(detections)
                samples.append((len(detections), annotate(pil, detections)))
                frames_sampled += 1
            index += 1
        cap.release()
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    inference_ms = int((time.perf_counter() - start) * 1000)
    if bundle is None:
        raise ValueError("No frames could be read from the video.")

    inspection = Inspection(
        product_ref=filename,
        category="detection_video",
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
            "counts": dict(counts),
            "total_defects": total_defects,
            "frames_sampled": frames_sampled,
        },
        inference_ms=inference_ms,
    )
    session.add(pred_row)
    session.commit()
    session.refresh(pred_row)

    # Keep the frames with the most detections as annotated samples.
    samples.sort(key=lambda item: item[0], reverse=True)
    frame_dir = get_settings().artifact_path / "detection_video" / str(pred_row.id)
    frame_dir.mkdir(parents=True, exist_ok=True)
    sample_urls: list[str] = []
    for i, (_, png) in enumerate(samples[:VIDEO_SAMPLE_FRAMES]):
        (frame_dir / f"{i}.png").write_bytes(png)
        sample_urls.append(f"/api/v1/explain/detection-frame/{pred_row.id}/{i}")

    return VideoDetectionResult(
        inspection_id=inspection.id,
        prediction_id=pred_row.id,
        frames_sampled=frames_sampled,
        total_defects=total_defects,
        counts=dict(counts),
        sample_frame_urls=sample_urls,
        model_version=bundle.version,
        is_fallback=bundle.is_fallback,
        inference_ms=inference_ms,
    )
