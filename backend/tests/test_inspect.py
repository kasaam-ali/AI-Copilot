"""Smoke tests for the image inspection endpoint (requires a trained image model)."""

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from ml import registry

pytestmark = pytest.mark.skipif(
    registry.get_active("image") is None,
    reason="No active image model; run training first.",
)


def _png_bytes() -> bytes:
    image = Image.new("RGB", (256, 256), (210, 210, 210))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_inspect_image_and_gradcam() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/inspect/image",
            files={"file": ("sample.png", _png_bytes(), "image/png")},
        )
        assert response.status_code == 200
        body = response.json()
        for key in (
            "inspection_id",
            "prediction_id",
            "label",
            "confidence",
            "uncertainty",
            "class_probs",
            "model_version",
            "weights_sha256",
            "gradcam_url",
        ):
            assert key in body

        gradcam = client.get(body["gradcam_url"])
        assert gradcam.status_code == 200
        assert gradcam.headers["content-type"].startswith("image/")


def test_inspect_rejects_non_image() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/inspect/image",
            files={"file": ("note.txt", b"hello", "text/plain")},
        )
        assert response.status_code == 415
