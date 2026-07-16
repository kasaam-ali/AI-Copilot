"""Inspection endpoints."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import Session

from app.database import get_session
from app.schemas.inspect import (
    ImageInspectionResult,
    SessionInspectionResult,
    TabularInspectionRequest,
    TabularInspectionResult,
    TabularSchema,
    TimeSeriesInspectionRequest,
    TimeSeriesInspectionResult,
)
from app.services.image_inference import run_image_inspection
from app.services.session_inference import run_session
from app.services.tabular_inference import get_tabular_schema, run_tabular_inspection
from app.services.timeseries_inference import run_timeseries_inspection

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


@router.post("/timeseries", response_model=TimeSeriesInspectionResult)
def inspect_timeseries(
    payload: TimeSeriesInspectionRequest,
    session: Session = Depends(get_session),
) -> TimeSeriesInspectionResult:
    try:
        return run_timeseries_inspection(session, payload.series)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post("/session", response_model=SessionInspectionResult)
async def inspect_session(
    image: UploadFile | None = File(default=None),
    tabular: str | None = Form(default=None),
    timeseries: str | None = Form(default=None),
    session: Session = Depends(get_session),
) -> SessionInspectionResult:
    """Multimodal hero endpoint: image file + JSON form fields for tabular/timeseries."""
    image_bytes: bytes | None = None
    if image is not None:
        if image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type: {image.content_type}",
            )
        image_bytes = await image.read()
        if len(image_bytes) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large (max 20 MB).",
            )

    try:
        tabular_features = json.loads(tabular) if tabular else None
        series = json.loads(timeseries)["series"] if timeseries else None
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid tabular/timeseries payload: {exc}",
        )

    try:
        return run_session(
            session,
            image_bytes=image_bytes,
            image_filename=image.filename if image is not None else None,
            tabular_features=tabular_features,
            series=series,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
