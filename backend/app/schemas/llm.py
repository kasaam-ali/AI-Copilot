"""DTOs for the LLM narrative and document-summary endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class LLMAttemptOut(BaseModel):
    provider: str
    ok: bool
    detail: str


class AnalyzeRequest(BaseModel):
    inspection_id: int


class AnalyzeResult(BaseModel):
    inspection_id: int
    root_cause: str
    contributing_factors: list[str]
    recommendations: list[str]
    confidence_note: str
    provider_used: str
    model: str | None
    attempts: list[LLMAttemptOut]


class DocSummaryResult(BaseModel):
    key_points: list[str]
    entities: list[str]
    risks: list[str]
    char_count: int
    provider_used: str
    model: str | None
    attempts: list[LLMAttemptOut]
