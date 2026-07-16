"""Tests for the active-learning retrain + human-gated activation flow (needs tabular)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from ml import registry

pytestmark = pytest.mark.skipif(
    registry.get_active("tabular") is None,
    reason="No active tabular model; run training first.",
)


def _make_correction(client: TestClient, corrected: str) -> None:
    defaults = client.get("/api/v1/inspect/tabular/schema").json()["defaults"]
    inspection_id = client.post("/api/v1/inspect/tabular", json={"features": defaults}).json()[
        "inspection_id"
    ]
    client.post(
        "/api/v1/feedback",
        json={"inspection_id": inspection_id, "decision": "modify", "corrected_label": corrected},
    )


def test_retrain_produces_inactive_version_then_activate() -> None:
    original_active = registry.get_active("tabular")["version"]
    with TestClient(app) as client:
        _make_correction(client, "defect")
        _make_correction(client, "ok")

        # Background task runs to completion within the TestClient request.
        job = client.post("/api/v1/retrain/tabular")
        assert job.status_code == 200
        job_id = job.json()["id"]

        detail = client.get(f"/api/v1/retrain/jobs/{job_id}").json()
        assert detail["status"] == "succeeded"
        assert detail["new_version"]
        assert detail["num_samples"] > 0
        assert "auroc_new" in detail["metrics"]
        new_version = detail["new_version"]

        versions = client.get("/api/v1/models/tabular").json()
        names = {v["version"] for v in versions["versions"]}
        assert new_version in names
        # New version is registered inactive; the original stays active until a human acts.
        assert versions["active"] == original_active

        activated = client.post(f"/api/v1/models/tabular/{new_version}/activate").json()
        assert activated["active"] == new_version

        # Predictions now report the newly activated version.
        result = client.post(
            "/api/v1/inspect/tabular",
            json={"features": client.get("/api/v1/inspect/tabular/schema").json()["defaults"]},
        ).json()
        assert result["model_version"] == new_version

        # Rollback keeps the demo on the original well-trained model.
        rolled = client.post(f"/api/v1/models/tabular/{original_active}/activate").json()
        assert rolled["active"] == original_active


def test_retrain_requires_a_correction() -> None:
    # A model type with no corrections should be rejected clearly.
    with TestClient(app) as client:
        response = client.post("/api/v1/retrain/image")
        assert response.status_code == 422
