"""Smoke test for the multimodal session endpoint (requires trained models)."""

import io
import json

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from ml import registry
from ml.timeseries.infer import load_active_bundle

pytestmark = pytest.mark.skipif(
    registry.get_active("image") is None
    or registry.get_active("tabular") is None
    or registry.get_active("timeseries") is None,
    reason="Session needs active image, tabular and timeseries models.",
)


def _png_bytes() -> bytes:
    image = Image.new("RGB", (256, 256), (200, 200, 200))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_session_fuses_three_modalities() -> None:
    with TestClient(app) as client:
        schema = client.get("/api/v1/inspect/tabular/schema").json()
        ts_bundle = load_active_bundle()
        series = [[70, 3.0, 55, 72, 12, 2.7][: len(ts_bundle.sensors)] for _ in range(ts_bundle.window)]

        response = client.post(
            "/api/v1/inspect/session",
            files={"image": ("sample.png", _png_bytes(), "image/png")},
            data={
                "tabular": json.dumps(schema["defaults"]),
                "timeseries": json.dumps({"series": series}),
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["health_score"] is not None
        assert 0.0 <= body["health_score"] <= 100.0
        assert body["health_band"] in {"healthy", "watch", "at_risk", "defect"}
        assert body["image"] and body["tabular"] and body["timeseries"]
        assert len(body["drivers"]) == 3
        assert body["errors"] == {}


def test_session_survives_with_one_modality() -> None:
    with TestClient(app) as client:
        ts_bundle = load_active_bundle()
        series = [[75, 3.5, 60, 74, 13, 2.6][: len(ts_bundle.sensors)] for _ in range(ts_bundle.window)]
        response = client.post(
            "/api/v1/inspect/session",
            data={"timeseries": json.dumps({"series": series})},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["timeseries"] is not None
        assert body["image"] is None and body["tabular"] is None
        assert len(body["drivers"]) == 1
