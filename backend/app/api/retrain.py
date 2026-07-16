"""Active-learning retrain endpoints."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.database import get_session
from app.models_db.models import RetrainJob
from app.schemas.retrain import RetrainJobOut
from app.services.active_learning import list_jobs, run_retrain_job, start_retrain

router = APIRouter(prefix="/retrain", tags=["active-learning"])


@router.post("/{model_type}", response_model=RetrainJobOut)
def trigger_retrain(
    model_type: str,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
) -> RetrainJob:
    try:
        job = start_retrain(session, model_type)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    background_tasks.add_task(run_retrain_job, job.id, model_type)
    return job


@router.get("/jobs", response_model=list[RetrainJobOut])
def get_jobs(
    model_type: str | None = Query(None),
    session: Session = Depends(get_session),
) -> list[RetrainJob]:
    return list_jobs(session, model_type)


@router.get("/jobs/{job_id}", response_model=RetrainJobOut)
def get_job(job_id: int, session: Session = Depends(get_session)) -> RetrainJob:
    job = session.get(RetrainJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job
