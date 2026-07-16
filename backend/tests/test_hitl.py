"""Tests for the human-in-the-loop review queue and feedback (needs a tabular model)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from ml import registry

pytestmark = pytest.mark.skipif(
    registry.get_active("tabular") is None,
    reason="No active tabular model; run training first.",
)


def _create_inspection(client: TestClient) -> int:
    defaults = client.get("/api/v1/inspect/tabular/schema").json()["defaults"]
    response = client.post("/api/v1/inspect/tabular", json={"features": defaults})
    assert response.status_code == 200
    return response.json()["inspection_id"]


def test_queue_detail_and_feedback() -> None:
    with TestClient(app) as client:
        inspection_id = _create_inspection(client)

        queue = client.get("/api/v1/inspections", params={"sort": "uncertainty"})
        assert queue.status_code == 200
        rows = queue.json()
        assert any(row["id"] == inspection_id for row in rows)
        # Uncertainty-sorted: non-null uncertainties are non-increasing.
        seen = [r["max_uncertainty"] for r in rows if r["max_uncertainty"] is not None]
        assert seen == sorted(seen, reverse=True)

        detail = client.get(f"/api/v1/inspections/{inspection_id}")
        assert detail.status_code == 200
        assert len(detail.json()["predictions"]) == 1

        feedback = client.post(
            "/api/v1/feedback",
            json={
                "inspection_id": inspection_id,
                "decision": "modify",
                "corrected_label": "ok",
                "note": "Verified within tolerance on the line.",
            },
        )
        assert feedback.status_code == 200
        assert feedback.json()["status"] == "modified"

        after = client.get(f"/api/v1/inspections/{inspection_id}").json()
        assert after["status"] == "modified"
        assert len(after["decisions"]) >= 1
        assert after["decisions"][0]["corrected_label"] == "ok"


def test_feedback_on_missing_inspection_404() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/feedback",
            json={"inspection_id": 99999999, "decision": "approve"},
        )
        assert response.status_code == 404
