"""Unit tests for the multimodal fusion maths (no models or DB required)."""

from app.models_db.models import HealthBand
from app.services.fusion import ModalitySignal, band_for, fuse


def test_empty_is_unknown() -> None:
    result = fuse({})
    assert result.health_score is None
    assert result.health_band is HealthBand.unknown
    assert result.drivers == []


def test_all_healthy_scores_high() -> None:
    signals = {
        "image": ModalitySignal(risk=0.0, uncertainty=0.05),
        "tabular": ModalitySignal(risk=0.05, uncertainty=0.05),
        "timeseries": ModalitySignal(risk=0.0, uncertainty=0.05),
    }
    result = fuse(signals)
    assert result.health_score is not None and result.health_score >= 95
    assert result.health_band is HealthBand.healthy


def test_all_defect_scores_low() -> None:
    signals = {
        "image": ModalitySignal(risk=0.98, uncertainty=0.02),
        "tabular": ModalitySignal(risk=0.9, uncertainty=0.02),
        "timeseries": ModalitySignal(risk=0.95, uncertainty=0.02),
    }
    result = fuse(signals)
    assert result.health_score is not None and result.health_score < 20
    assert result.health_band is HealthBand.defect


def test_missing_modality_renormalizes() -> None:
    # Only tabular present: score reflects tabular risk alone, not diluted by absent ones.
    signals = {"tabular": ModalitySignal(risk=1.0, uncertainty=0.0)}
    result = fuse(signals)
    assert result.health_score == 0.0
    assert len(result.drivers) == 1
    assert result.drivers[0]["modality"] == "tabular"


def test_high_uncertainty_reduces_influence() -> None:
    confident = fuse({
        "image": ModalitySignal(risk=1.0, uncertainty=0.0),
        "tabular": ModalitySignal(risk=0.0, uncertainty=0.0),
    })
    uncertain = fuse({
        "image": ModalitySignal(risk=1.0, uncertainty=5.0),
        "tabular": ModalitySignal(risk=0.0, uncertainty=0.0),
    })
    # A very uncertain high-risk image should drag the score down less.
    assert uncertain.health_score > confident.health_score


def test_drivers_sorted_by_contribution() -> None:
    result = fuse({
        "image": ModalitySignal(risk=0.2, uncertainty=0.0),
        "tabular": ModalitySignal(risk=0.9, uncertainty=0.0),
    })
    contributions = [d["contribution"] for d in result.drivers]
    assert contributions == sorted(contributions, reverse=True)


def test_band_boundaries() -> None:
    assert band_for(80) is HealthBand.healthy
    assert band_for(79.9) is HealthBand.watch
    assert band_for(60) is HealthBand.watch
    assert band_for(59.9) is HealthBand.at_risk
    assert band_for(40) is HealthBand.at_risk
    assert band_for(39.9) is HealthBand.defect
    assert band_for(None) is HealthBand.unknown
