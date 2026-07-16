"""Prompts, strict-JSON validators and the repair hint for the LLM layer."""

from __future__ import annotations

import json

REPAIR_HINT = (
    "Your previous reply was not valid JSON. Reply again with ONLY a single JSON object "
    "matching the requested keys — no prose, no markdown, no code fences."
)

ANALYZE_SYSTEM = (
    "You are a senior manufacturing quality analyst. You are given the structured outputs "
    "of predictive models (a fused health score and per-modality signals). You do NOT make "
    "predictions yourself — you explain and act on the numbers provided. Reply with ONLY a "
    "JSON object with keys: root_cause (string), contributing_factors (array of strings), "
    "recommendations (array of strings), confidence_note (string). Be concise, specific and "
    "grounded strictly in the provided evidence."
)

SUMMARY_SYSTEM = (
    "You extract structured information from a manufacturing / maintenance document. Reply "
    "with ONLY a JSON object with keys: key_points (array of strings), entities (array of "
    "strings), risks (array of strings). Keep each item short and grounded in the text."
)


def build_analyze_user(context: dict) -> str:
    return (
        "Evidence from the inspection (JSON):\n"
        + json.dumps(context, indent=2)
        + "\n\nExplain the most likely root cause of the health score, the contributing "
        "factors (cite the modalities and drivers above), and concrete recommendations for "
        "the line operator. Return the JSON object described in the system message."
    )


def build_summary_user(text: str) -> str:
    return (
        "Document text:\n\"\"\"\n"
        + text
        + "\n\"\"\"\n\nSummarize it as the JSON object described in the system message."
    )


def _as_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("expected a list")
    return [str(item) for item in value]


def validate_analyze(text: str) -> dict:
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("root is not an object")
    return {
        "root_cause": str(data["root_cause"]),
        "contributing_factors": _as_str_list(data.get("contributing_factors", [])),
        "recommendations": _as_str_list(data.get("recommendations", [])),
        "confidence_note": str(data.get("confidence_note", "")),
    }


def validate_summary(text: str) -> dict:
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("root is not an object")
    return {
        "key_points": _as_str_list(data.get("key_points", [])),
        "entities": _as_str_list(data.get("entities", [])),
        "risks": _as_str_list(data.get("risks", [])),
    }
