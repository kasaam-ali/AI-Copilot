"""Tests for the LLM fallback chain, validators and mock (no network required)."""

from types import SimpleNamespace

import pytest

from app.services.llm import chain
from app.services.llm.base import ProviderError
from app.services.llm.chain import FallbackLLMService
from app.services.llm.mock import mock_analysis, mock_summary
from app.services.llm.prompts import validate_analyze, validate_summary


class FakeProvider:
    def __init__(self, name: str, behavior):
        self.name = name
        self.model = f"{name}-model"
        self._behavior = behavior

    def complete(self, system, user, *, timeout, json_mode=True):  # noqa: ARG002
        result = self._behavior(user)
        if isinstance(result, Exception):
            raise result
        return result


def _force(monkeypatch, order, providers: dict):
    monkeypatch.setattr(
        chain,
        "get_settings",
        lambda: SimpleNamespace(provider_order=order, llm_timeout_seconds=5.0),
    )
    monkeypatch.setattr(chain, "_build_provider", lambda name, settings: providers.get(name))
    chain._circuit.clear()


VALID = '{"key_points": ["a"], "entities": ["X"], "risks": ["r"]}'


def test_mock_analysis_is_grounded() -> None:
    context = {
        "health_score": 42.0,
        "health_band": "at_risk",
        "modalities": {"tabular": {"_name": "the process-data model", "defect_probability": 0.7, "top_drivers": [{"feature": "vibration_rms"}]}},
    }
    result = mock_analysis(context)
    assert "42" in result["root_cause"]
    assert result["recommendations"]
    assert "offline" in result["confidence_note"].lower()


def test_validate_summary_rejects_bad_json() -> None:
    assert validate_summary(VALID)["key_points"] == ["a"]
    with pytest.raises(ValueError):
        validate_summary("not json")


def test_validate_analyze_requires_root_cause() -> None:
    with pytest.raises(KeyError):
        validate_analyze('{"recommendations": []}')


def test_chain_uses_first_working_provider(monkeypatch) -> None:
    providers = {
        "groq": FakeProvider("groq", lambda user: VALID),
        "zai": FakeProvider("zai", lambda user: VALID),
    }
    _force(monkeypatch, ["groq", "zai", "mock"], providers)
    result = FallbackLLMService().complete_json(
        system="s", user="u", validate=validate_summary, fallback=lambda: {"key_points": [], "entities": [], "risks": []}
    )
    assert result.provider_used == "groq"
    assert result.attempts[-1].ok


def test_chain_cascades_to_next_then_mock(monkeypatch) -> None:
    providers = {
        "groq": FakeProvider("groq", lambda user: ProviderError("groq down")),
        "zai": FakeProvider("zai", lambda user: "still not json"),
    }
    _force(monkeypatch, ["groq", "zai", "mock"], providers)
    result = FallbackLLMService().complete_json(
        system="s",
        user="u",
        validate=validate_summary,
        fallback=lambda: mock_summary("Bearing wear is a risk. Inspect the spindle."),
    )
    assert result.provider_used == "mock"
    # groq transport-failed, zai invalid-JSON (after repair), then mock.
    details = {a.provider: a for a in result.attempts}
    assert details["groq"].ok is False
    assert details["zai"].ok is False
    assert details["mock"].ok is True
    assert result.data["risks"]


def test_missing_key_provider_is_skipped(monkeypatch) -> None:
    providers = {"groq": None, "zai": FakeProvider("zai", lambda user: VALID)}
    _force(monkeypatch, ["groq", "zai", "mock"], providers)
    result = FallbackLLMService().complete_json(
        system="s", user="u", validate=validate_summary, fallback=lambda: {"key_points": [], "entities": [], "risks": []}
    )
    assert result.provider_used == "zai"
