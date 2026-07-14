"""Smoke tests for the health and readiness endpoints."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_liveness() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_readiness() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is True
    assert body["checks"]["database"] is True
    assert body["checks"]["artifacts_writable"] is True


def test_request_id_header_present() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
    assert "X-Request-ID" in response.headers
