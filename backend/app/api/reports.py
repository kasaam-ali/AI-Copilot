"""Report generation and download endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.database import get_session
from app.services.report_service import generate_report, list_reports

router = APIRouter(prefix="/reports", tags=["reports"])

_MEDIA = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.get("")
def get_reports() -> list[dict]:
    return list_reports()


@router.post("/{inspection_id}")
def create_report(
    inspection_id: int,
    fmt: str = Query("pdf", alias="format", pattern="^(pdf|docx)$"),
    session: Session = Depends(get_session),
) -> dict:
    try:
        path = generate_report(session, inspection_id, fmt)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return {
        "inspection_id": inspection_id,
        "format": fmt,
        "size_bytes": path.stat().st_size,
        "download_url": f"/api/v1/reports/{inspection_id}/download?format={fmt}",
    }


@router.get("/{inspection_id}/download")
def download_report(
    inspection_id: int,
    fmt: str = Query("pdf", alias="format", pattern="^(pdf|docx)$"),
    session: Session = Depends(get_session),
) -> FileResponse:
    try:
        path = generate_report(session, inspection_id, fmt)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return FileResponse(path, media_type=_MEDIA[fmt], filename=path.name)
