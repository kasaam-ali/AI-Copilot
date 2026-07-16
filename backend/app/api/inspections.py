"""Inspection listing and detail endpoints for the review queue."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.database import get_session
from app.schemas.review import InspectionDetail, InspectionSummary
from app.services.hitl_service import get_inspection_detail, list_inspections

router = APIRouter(prefix="/inspections", tags=["review"])


@router.get("", response_model=list[InspectionSummary])
def get_inspections(
    sort: str = Query("uncertainty", pattern="^(uncertainty|recent)$"),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> list[InspectionSummary]:
    return list_inspections(session, sort=sort, status=status_filter, limit=limit)


@router.get("/{inspection_id}", response_model=InspectionDetail)
def get_inspection(
    inspection_id: int,
    session: Session = Depends(get_session),
) -> InspectionDetail:
    detail = get_inspection_detail(session, inspection_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
    return detail
