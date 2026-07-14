"""Health and readiness endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlmodel import Session

from app.config import Settings, get_settings
from app.database import get_session

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict:
    """Liveness probe."""
    return {"status": "ok", "service": "SentinelQ"}


@router.get("/health/ready")
def health_ready(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Readiness probe: verify the database is reachable and artifacts are writable."""
    checks: dict[str, bool] = {}

    try:
        session.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:  # noqa: BLE001
        checks["database"] = False

    try:
        artifact_dir = settings.artifact_path
        artifact_dir.mkdir(parents=True, exist_ok=True)
        probe = artifact_dir / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        checks["artifacts_writable"] = True
    except Exception:  # noqa: BLE001
        checks["artifacts_writable"] = False

    return {"ready": all(checks.values()), "checks": checks}
