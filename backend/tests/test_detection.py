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
