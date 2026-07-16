"""Multimodal fusion into a single Health Score.

Pure functions (no I/O), so the fusion maths is unit-testable in isolation. Each present
modality contributes a defect/degradation risk in [0, 1] and an uncertainty sigma. More
certain modalities count for more; the score renormalizes over whichever modalities are
present, so a missing or failed modality simply drops out.

    health = 100 * (1 - sum(w_i * c_i * r_i) / sum(w_i * c_i))
    c_i    = 1 / (1 + sigma_i)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models_db.models import HealthBand

# Config-driven in Settings later; the vision model is weighted highest.
MODALITY_WEIGHTS: dict[str, float] = {
    "image": 0.45,
    "tabular": 0.30,
    "timeseries": 0.25,
}


@dataclass
class ModalitySignal:
    risk: float
    uncertainty: float


@dataclass
class FusionResult:
    health_score: float | None
    health_band: HealthBand
    drivers: list[dict] = field(default_factory=list)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def band_for(score: float | None) -> HealthBand:
    if score is None:
        return HealthBand.unknown
    if score >= 80:
        return HealthBand.healthy
    if score >= 60:
        return HealthBand.watch
    if score >= 40:
        return HealthBand.at_risk
    return HealthBand.defect


def fuse(signals: dict[str, ModalitySignal]) -> FusionResult:
    """Fuse present modality signals into a health score, band and ranked drivers."""
    present = {name: sig for name, sig in signals.items() if sig is not None}
    if not present:
        return FusionResult(health_score=None, health_band=HealthBand.unknown, drivers=[])

    numerator = 0.0
    denominator = 0.0
    drivers: list[dict] = []
    for name, sig in present.items():
        weight = MODALITY_WEIGHTS.get(name, 0.0)
        risk = _clamp01(sig.risk)
        confidence_weight = 1.0 / (1.0 + max(0.0, sig.uncertainty))
        contribution = weight * confidence_weight * risk
        numerator += contribution
        denominator += weight * confidence_weight
        drivers.append(
            {
                "modality": name,
                "weight": weight,
                "risk": risk,
                "uncertainty": sig.uncertainty,
                "confidence_weight": confidence_weight,
                "contribution": contribution,
            }
        )

    score = 100.0 * (1.0 - numerator / denominator) if denominator > 0 else None
    for driver in drivers:
        driver["share"] = driver["contribution"] / numerator if numerator > 0 else 0.0
    drivers.sort(key=lambda item: item["contribution"], reverse=True)

    return FusionResult(health_score=score, health_band=band_for(score), drivers=drivers)
