"""Deterministic, offline builders used as the terminal fallback.

These never call the network and never raise. They read the same structured evidence the
real providers get, so the narrative stays grounded even without any API key.
"""

from __future__ import annotations

import re

_BAND_PHRASE = {
    "healthy": "no significant quality risk",
    "watch": "an early, watch-level quality risk",
    "at_risk": "an elevated quality risk that warrants attention",
    "defect": "a strong defect signal requiring immediate action",
    "unknown": "an inconclusive result",
}


def mock_analysis(context: dict) -> dict:
    """Build a grounded analysis dict directly from the fused evidence."""
    band = context.get("health_band", "unknown")
    score = context.get("health_score")
    modalities: dict = context.get("modalities", {})

    factors: list[str] = []
    recommendations: list[str] = []

    image = modalities.get("image")
    if image:
        prob = image.get("defect_probability", 0.0)
        factors.append(f"Vision model flags the product as '{image.get('label')}' ({prob:.0%} defect probability).")
        if prob >= 0.5:
            recommendations.append("Quarantine the unit and re-image under controlled lighting.")

    tabular = modalities.get("tabular")
    if tabular:
        drivers = ", ".join(d["feature"] for d in tabular.get("top_drivers", [])[:3]) or "process parameters"
        factors.append(f"Process data gives {tabular.get('defect_probability', 0.0):.0%} defect probability, driven by {drivers}.")
        recommendations.append(f"Verify {drivers} against setpoints on the line.")

    timeseries = modalities.get("timeseries")
    if timeseries:
        sensors = ", ".join(s["sensor"] for s in timeseries.get("top_sensors", [])[:3]) or "the monitored sensors"
        factors.append(
            f"Machine health estimates {timeseries.get('rul', 0):.0f} cycles of remaining life "
            f"({timeseries.get('risk', 0.0):.0%} failure risk), most influenced by {sensors}."
        )
        if timeseries.get("risk", 0.0) >= 0.5:
            recommendations.append(f"Schedule maintenance; inspect {sensors} for wear.")

    if not recommendations:
        recommendations.append("Continue routine monitoring; no immediate action required.")

    strongest = max(
        (m for m in (image, tabular, timeseries) if m),
        key=lambda m: m.get("defect_probability", m.get("risk", 0.0)),
        default=None,
    )
    lead = "the combined evidence"
    if strongest is not None:
        lead = strongest.get("_name", "the combined evidence")

    score_text = f"{score:.0f}/100" if isinstance(score, (int, float)) else "unavailable"
    return {
        "root_cause": (
            f"The fused health score is {score_text} ({band}), indicating {_BAND_PHRASE.get(band, 'an inconclusive result')}. "
            f"The signal is led by {lead}."
        ),
        "contributing_factors": factors or ["No modality data was available for this inspection."],
        "recommendations": recommendations,
        "confidence_note": (
            "Deterministic offline analysis (no LLM provider reached). Figures are taken "
            "directly from the model outputs and uncertainty estimates."
        ),
    }


def mock_summary(text: str) -> dict:
    """Extractive fallback summary: first sentences, simple entities and risk lines."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 20]
    key_points = sentences[:5]

    entities = sorted(set(re.findall(r"\b[A-Z][A-Za-z0-9\-]{2,}\b", text)))[:10]
    risk_words = ("risk", "fail", "defect", "fault", "hazard", "warning", "critical", "wear")
    risks = [s for s in sentences if any(word in s.lower() for word in risk_words)][:5]

    return {
        "key_points": key_points or ["No extractable key points."],
        "entities": entities,
        "risks": risks or ["No explicit risks detected in the text."],
    }
