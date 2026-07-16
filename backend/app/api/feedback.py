"""Human-in-the-loop feedback endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.database import get_session
from app.schemas.review import FeedbackRequest, FeedbackResult
from app.services.hitl_service import record_feedback

router = APIRouter(prefix="/feedback", tags=["review"])


@router.post("", response_model=FeedbackResult)
def submit_feedback(
    payload: FeedbackRequest,
    session: Session = Depends(get_session),
) -> FeedbackResult:
    try:
        return record_feedback(session, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
