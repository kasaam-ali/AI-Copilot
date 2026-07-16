"""Tests for LLM analysis, document summary and report generation (offline via mock)."""

import io
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.llm import chain
from ml import registry

pytestmark = pytest.mark.skipif(
    registry.get_active("tabular") is None,
    reason="No active tabular model; run training first.",
)


@pytest.fixture(autouse=True)
def _force_mock(monkeypatch):
    """Keep tests offline and deterministic by forcing the mock provider."""
    monkeypatch.setattr(
        chain,
        "get_settings",
        lambda: SimpleNamespace(provider_order=["mock"], llm_timeout_seconds=5.0),
    )


def _tabular_inspection(client: TestClient) -> int:
    defaults = client.get("/api/v1/inspect/tabular/schema").json()["defaults"]
    return client.post("/api/v1/inspect/tabular", json={"features": defaults}).json()["inspection_id"]


def _sample_pdf() -> bytes:
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 800, "Maintenance log: spindle vibration rising over the last shift.")
    pdf.drawString(72, 780, "Risk of bearing failure if tool wear exceeds the threshold.")
    pdf.save()
    return buffer.getvalue()


def test_analyze_then_report_pdf_and_docx() -> None:
    with TestClient(app) as client:
        inspection_id = _tabular_inspection(client)

        analyze = client.post("/api/v1/llm/analyze", json={"inspection_id": inspection_id})
        assert analyze.status_code == 200
        body = analyze.json()
        assert body["provider_used"] == "mock"
        assert body["root_cause"]
        assert isinstance(body["recommendations"], list)

        pdf = client.post(f"/api/v1/reports/{inspection_id}", params={"format": "pdf"})
        assert pdf.status_code == 200
        assert pdf.json()["size_bytes"] > 0

        docx = client.get(f"/api/v1/reports/{inspection_id}/download", params={"format": "docx"})
        assert docx.status_code == 200
        assert "wordprocessingml" in docx.headers["content-type"]
        assert len(docx.content) > 0

        listing = client.get("/api/v1/reports").json()
        assert any(r["inspection_id"] == inspection_id for r in listing)


def test_summarize_document() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/llm/summarize-doc",
            files={"file": ("log.pdf", _sample_pdf(), "application/pdf")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["provider_used"] == "mock"
        assert body["key_points"]
        assert body["char_count"] > 0
