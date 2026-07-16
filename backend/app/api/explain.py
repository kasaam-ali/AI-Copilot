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


@router.get("/detection/{prediction_id}")
def get_detection(prediction_id: int, session: Session = Depends(get_session)) -> FileResponse:
    prediction = session.get(Prediction, prediction_id)
    if prediction is None or not prediction.artifact_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Annotated image not found")
    path = Path(prediction.artifact_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Annotated file missing")
    return FileResponse(path, media_type="image/png")


@router.get("/detection-frame/{prediction_id}/{index}")
def get_detection_frame(
    prediction_id: int, index: int, session: Session = Depends(get_session)
) -> FileResponse:
    from app.config import get_settings

    path = get_settings().artifact_path / "detection_video" / str(prediction_id) / f"{index}.png"
    if session.get(Prediction, prediction_id) is None or not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Frame not found")
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


@router.get("/timeseries/{prediction_id}")
def get_timeseries(prediction_id: int, session: Session = Depends(get_session)) -> dict:
    prediction = session.get(Prediction, prediction_id)
    if (
        prediction is None
        or not prediction.raw_scores
        or "attributions" not in prediction.raw_scores
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attributions not found")
    return {
        "sensors": prediction.raw_scores.get("sensors"),
        "attributions": prediction.raw_scores["attributions"],
        "sensor_importance": prediction.raw_scores.get("sensor_importance"),
        "rul": prediction.raw_scores.get("rul"),
    }
