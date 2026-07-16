"""Smoke tests for the tabular inspection endpoint (requires a trained tabular model)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from ml import registry

pytestmark = pytest.mark.skipif(
    registry.get_active("tabular") is None,
    reason="No active tabular model; run training first.",
)


def test_tabular_schema_inspect_and_shap() -> None:
    with TestClient(app) as client:
        schema = client.get("/api/v1/inspect/tabular/schema")
        assert schema.status_code == 200
        defaults = schema.json()["defaults"]
        assert schema.json()["features"]
        assert defaults

        response = client.post("/api/v1/inspect/tabular", json={"features": defaults})
        assert response.status_code == 200
        body = response.json()
        for key in (
            "inspection_id",
            "prediction_id",
            "label",
            "defect_probability",
            "confidence",
            "uncertainty",
            "base_value",
            "shap",
            "model_version",
        ):
            assert key in body
        assert len(body["shap"]) > 0

        shap_response = client.get(f"/api/v1/explain/shap/{body['prediction_id']}")
        assert shap_response.status_code == 200
        assert "shap" in shap_response.json()


def test_tabular_batch_scores_many() -> None:
    with TestClient(app) as client:
        defaults = client.get("/api/v1/inspect/tabular/schema").json()["defaults"]
        response = client.post(
            "/api/v1/inspect/tabular/batch",
            json={"rows": [defaults, defaults, defaults]},
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["results"]) == 3
        for row in body["results"]:
            assert "label" in row and "defect_probability" in row
            assert 0.0 <= row["defect_probability"] <= 1.0
