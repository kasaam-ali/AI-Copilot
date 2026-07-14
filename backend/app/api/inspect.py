"""Inspection endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlmodel import Session

from app.database import get_session
from app.schemas.inspect import (
    ImageInspectionResult,
    TabularInspectionRequest,
    TabularInspectionResult,
    TabularSchema,
)
from app.services.image_inference import run_image_inspection
from app.services.tabular_inference import get_tabular_schema, run_tabular_inspection

router = APIRouter(prefix="/inspect", tags=["inspection"])

ALLOWED_IMAGE_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/bmp",
    "image/webp",
}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


@router.post("/image", response_model=ImageInspectionResult)
async def inspect_image(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> ImageInspectionResult:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}",
        )
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (max 20 MB).",
        )
    try:
        return run_image_inspection(session, data, file.filename)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.get("/tabular/schema", response_model=TabularSchema)
def tabular_schema() -> TabularSchema:
    try:
        return get_tabular_schema()
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.post("/tabular", response_model=TabularInspectionResult)
def inspect_tabular(
    payload: TabularInspectionRequest,
    session: Session = Depends(get_session),
) -> TabularInspectionResult:
    try:
        return run_tabular_inspection(session, payload.features)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
