"""Fallback LLM service: try providers in order, always terminate in the mock.

Cascades to the next provider on a missing key, transport error, HTTP error, timeout or
schema-invalid response (with one repair retry per provider). A provider that fails twice is
short-circuited for a cooldown window. The terminal ``mock`` provider is deterministic and
never raises, so ``complete_json`` always returns a valid result.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable

from loguru import logger

from app.config import Settings, get_settings
from app.services.llm.base import (
    LLMAttempt,
    LLMResult,
    ProviderError,
    ProviderUnavailable,
)
from app.services.llm.openai_compatible import OpenAICompatibleProvider

_BREAKER_THRESHOLD = 2
_BREAKER_COOLDOWN = 60.0
_circuit: dict[str, tuple[int, float]] = {}

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def _strip_fences(text: str) -> str:
    stripped = text.strip()
    stripped = _FENCE.sub("", stripped)
    return stripped.strip()


def _build_provider(name: str, settings: Settings) -> OpenAICompatibleProvider | None:
    specs = {
        "groq": (settings.groq_base_url, settings.groq_api_key, settings.groq_model, None),
        "openrouter": (
            settings.openrouter_base_url,
            settings.openrouter_api_key,
            settings.openrouter_model,
            {"HTTP-Referer": "https://sentinelq.local", "X-Title": "SentinelQ"},
        ),
        "zai": (settings.zai_base_url, settings.zai_api_key, settings.zai_model, None),
        "gemini": (settings.gemini_base_url, settings.gemini_api_key, settings.gemini_model, None),
    }
    spec = specs.get(name)
    if spec is None:
        return None
    base_url, api_key, model, headers = spec
    return OpenAICompatibleProvider(name, base_url, api_key, model, extra_headers=headers)


def _breaker_open(name: str) -> bool:
    state = _circuit.get(name)
    return bool(state and state[1] > time.time())


def _record_failure(name: str) -> None:
    count = _circuit.get(name, (0, 0.0))[0] + 1
    until = time.time() + _BREAKER_COOLDOWN if count >= _BREAKER_THRESHOLD else 0.0
    _circuit[name] = (count, until)


def _record_success(name: str) -> None:
    _circuit.pop(name, None)


class FallbackLLMService:
    def complete_json(
        self,
        *,
        system: str,
        user: str,
        validate: Callable[[str], dict],
        fallback: Callable[[], dict],
    ) -> LLMResult:
        settings = get_settings()
        attempts: list[LLMAttempt] = []

        for name in settings.provider_order:
            if name == "mock":
                attempts.append(LLMAttempt("mock", True, "deterministic fallback"))
                return LLMResult(fallback(), "mock", None, attempts)

            if _breaker_open(name):
                attempts.append(LLMAttempt(name, False, "circuit open (recent failures)"))
                continue

            provider = _build_provider(name, settings)
            if provider is None:
                attempts.append(LLMAttempt(name, False, "unknown provider"))
                continue

            timeout = settings.llm_timeout_seconds
            try:
                raw = provider.complete(system, user, timeout=timeout, json_mode=True)
            except ProviderUnavailable as exc:
                attempts.append(LLMAttempt(name, False, str(exc)))
                continue
            except ProviderError as exc:
                _record_failure(name)
                attempts.append(LLMAttempt(name, False, str(exc)))
                logger.warning("LLM provider {} failed: {}", name, exc)
                continue

            try:
                data = validate(_strip_fences(raw))
                _record_success(name)
                attempts.append(LLMAttempt(name, True, "ok"))
                return LLMResult(data, name, provider.model, attempts)
            except (ValueError, KeyError, TypeError):
                # One repair retry: ask the same provider for strict JSON.
                try:
                    from app.services.llm.prompts import REPAIR_HINT

                    raw = provider.complete(
                        system, f"{user}\n\n{REPAIR_HINT}", timeout=timeout, json_mode=True
                    )
                    data = validate(_strip_fences(raw))
                    _record_success(name)
                    attempts.append(LLMAttempt(name, True, "ok after repair"))
                    return LLMResult(data, name, provider.model, attempts)
                except Exception as exc:  # noqa: BLE001 - cascade on any repair failure
                    _record_failure(name)
                    attempts.append(LLMAttempt(name, False, f"invalid JSON: {exc}"))
                    continue

        # No mock in the order — still guarantee a result.
        attempts.append(LLMAttempt("mock", True, "forced fallback"))
        return LLMResult(fallback(), "mock", None, attempts)


_service: FallbackLLMService | None = None


def get_llm_service() -> FallbackLLMService:
    global _service
    if _service is None:
        _service = FallbackLLMService()
    return _service
