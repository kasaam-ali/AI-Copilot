"""Model version listing and human-gated activation."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.retrain import ModelVersionsOut
from app.services.active_learning import activate_version, list_versions

router = APIRouter(prefix="/models", tags=["active-learning"])


@router.get("/{model_type}", response_model=ModelVersionsOut)
def get_versions(model_type: str) -> dict:
    return list_versions(model_type)


@router.post("/{model_type}/{version}/activate", response_model=ModelVersionsOut)
def activate(model_type: str, version: str) -> dict:
    try:
        return activate_version(model_type, version)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
