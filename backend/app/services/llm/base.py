"""Core types for the LLM layer."""

from __future__ import annotations

from dataclasses import dataclass


class ProviderError(Exception):
    """A provider failed to produce a usable response (transport, HTTP, bad body)."""


class ProviderUnavailable(ProviderError):
    """A provider is not configured (e.g. missing API key) and should be skipped."""


@dataclass
class LLMAttempt:
    provider: str
    ok: bool
    detail: str


@dataclass
class LLMResult:
    data: dict
    provider_used: str
    model: str | None
    attempts: list[LLMAttempt]


class LLMProvider:
    """Interface: turn a system + user prompt into raw text, or raise ProviderError."""

    name: str
    model: str

    def complete(self, system: str, user: str, *, timeout: float, json_mode: bool = True) -> str:
        raise NotImplementedError
