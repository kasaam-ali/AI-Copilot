"""Document summarization — the fourth modality (text).

Extracts text from an uploaded PDF and asks the LLM layer to structure it (key points,
entities, risks), with the same deterministic offline fallback as the analysis service.
"""

from __future__ import annotations

import io

from app.schemas.llm import DocSummaryResult, LLMAttemptOut
from app.services.llm import get_llm_service
from app.services.llm.mock import mock_summary
from app.services.llm.prompts import SUMMARY_SYSTEM, build_summary_user, validate_summary

_MAX_CHARS = 8000


def extract_pdf_text(file_bytes: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(file_bytes))
    parts = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(parts).strip()


def summarize_document(file_bytes: bytes) -> DocSummaryResult:
    text = extract_pdf_text(file_bytes)
    if not text:
        raise ValueError("No extractable text found in the PDF.")

    truncated = text[:_MAX_CHARS]
    result = get_llm_service().complete_json(
        system=SUMMARY_SYSTEM,
        user=build_summary_user(truncated),
        validate=validate_summary,
        fallback=lambda: mock_summary(truncated),
    )

    return DocSummaryResult(
        char_count=len(text),
        provider_used=result.provider_used,
        model=result.model,
        attempts=[LLMAttemptOut(**a.__dict__) for a in result.attempts],
        **result.data,
    )
