"""Smoke tests for the time-series endpoint (requires a trained timeseries model)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from ml import registry
from ml.timeseries.infer import load_active_bundle

pytestmark = pytest.mark.skipif(
    registry.get_active("timeseries") is None,
    reason="No active timeseries model; run training first.",
)


def _sample_series(level: float) -> list[list[float]]:
    bundle = load_active_bundle()
    return [[level] * len(bundle.sensors) for _ in range(bundle.window)]


def test_timeseries_inspect_and_explain() -> None:
    with TestClient(app) as client:
        bundle = load_active_bundle()
        series = [
            [80, 4.0, 72, 80, 15, 2.3][: len(bundle.sensors)] for _ in range(bundle.window)
        ]
        response = client.post("/api/v1/inspect/timeseries", json={"series": series})
        assert response.status_code == 200
        body = response.json()
        for key in ("inspection_id", "prediction_id", "rul", "risk", "sensors", "sensor_importance"):
            assert key in body
        assert 0.0 <= body["risk"] <= 1.0
        assert len(body["sensor_importance"]) > 0

        explain = client.get(f"/api/v1/explain/timeseries/{body['prediction_id']}")
        assert explain.status_code == 200
        assert len(explain.json()["attributions"]) == bundle.window


def test_short_series_is_accepted() -> None:
    with TestClient(app) as client:
        bundle = load_active_bundle()
        series = [[60] * len(bundle.sensors)]  # single timestep, front-padded
        response = client.post("/api/v1/inspect/timeseries", json={"series": series})
        assert response.status_code == 200
