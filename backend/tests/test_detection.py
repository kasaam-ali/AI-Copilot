"""Tests for the YOLO defect-detection endpoint (uses the pretrained fallback)."""

import importlib.util
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("ultralytics") is None,
    reason="ultralytics not installed",
)


def _png() -> bytes:
    image = Image.new("RGB", (320, 320), (120, 120, 120))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_detect_returns_structure_and_annotated_image() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/inspect/detect",
            files={"file": ("sample.png", _png(), "image/png")},
        )
        assert response.status_code == 200
        body = response.json()
        for key in (
            "inspection_id",
            "prediction_id",
            "detections",
            "counts",
            "n_defects",
            "annotated_url",
            "model_version",
            "is_fallback",
        ):
            assert key in body
        assert body["n_defects"] == len(body["detections"])

        annotated = client.get(body["annotated_url"])
        assert annotated.status_code == 200
        assert annotated.headers["content-type"].startswith("image/")


def test_detect_rejects_non_image() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/inspect/detect",
            files={"file": ("note.txt", b"hello", "text/plain")},
        )
        assert response.status_code == 415


def _short_avi() -> bytes:
    import os
    import tempfile

    import cv2
    import numpy as np

    frame = np.full((240, 320, 3), 120, dtype=np.uint8)
    path = os.path.join(tempfile.gettempdir(), "sq_test_clip.avi")
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 5, (320, 240))
    for _ in range(10):
        writer.write(frame)
    writer.release()
    with open(path, "rb") as fh:
        data = fh.read()
    os.unlink(path)
    return data


def test_frame_detection_is_stateless() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/inspect/frame",
            files={"file": ("frame.jpg", _png(), "image/jpeg")},
        )
        assert response.status_code == 200
        body = response.json()
        for key in ("detections", "width", "height", "model_version", "is_fallback"):
            assert key in body
        assert body["width"] > 0 and body["height"] > 0


def test_detect_video_aggregates_frames() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/inspect/detect/video",
            files={"file": ("clip.avi", _short_avi(), "video/x-msvideo")},
        )
        assert response.status_code == 200
        body = response.json()
        for key in ("frames_sampled", "total_defects", "counts", "sample_frame_urls", "model_version"):
            assert key in body
        assert body["frames_sampled"] > 0
        for url in body["sample_frame_urls"]:
            frame = client.get(url)
            assert frame.status_code == 200
            assert frame.headers["content-type"].startswith("image/")
