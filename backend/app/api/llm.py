"""LLM narrative and document-summary endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlmodel import Session

from app.database import get_session
from app.schemas.llm import AnalyzeRequest, AnalyzeResult, DocSummaryResult
from app.services.analysis_service import analyze_inspection
from app.services.doc_summary_service import summarize_document

router = APIRouter(prefix="/llm", tags=["llm"])

MAX_PDF_BYTES = 15 * 1024 * 1024


@router.post("/analyze", response_model=AnalyzeResult)
def analyze(payload: AnalyzeRequest, session: Session = Depends(get_session)) -> AnalyzeResult:
    try:
        return analyze_inspection(session, payload.inspection_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/summarize-doc", response_model=DocSummaryResult)
async def summarize_doc(file: UploadFile = File(...)) -> DocSummaryResult:
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Expected a PDF, got {file.content_type}",
        )
    data = await file.read()
    if len(data) > MAX_PDF_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="PDF too large (max 15 MB)."
        )
    try:
        return summarize_document(data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
