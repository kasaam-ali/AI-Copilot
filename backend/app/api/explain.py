"""Explainability artifact endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.database import get_session
from app.models_db.models import Prediction

router = APIRouter(prefix="/explain", tags=["explainability"])


@router.get("/gradcam/{prediction_id}")
def get_gradcam(prediction_id: int, session: Session = Depends(get_session)) -> FileResponse:
    prediction = session.get(Prediction, prediction_id)
    if prediction is None or not prediction.artifact_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grad-CAM not found")
    path = Path(prediction.artifact_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grad-CAM file missing")
    return FileResponse(path, media_type="image/png")


@router.get("/shap/{prediction_id}")
def get_shap(prediction_id: int, session: Session = Depends(get_session)) -> dict:
    prediction = session.get(Prediction, prediction_id)
    if prediction is None or not prediction.raw_scores or "shap" not in prediction.raw_scores:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SHAP not found")
    return {
        "base_value": prediction.raw_scores.get("base_value"),
        "shap": prediction.raw_scores["shap"],
    }
