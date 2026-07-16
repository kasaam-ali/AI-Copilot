"""One OpenAI-compatible chat client for Groq, OpenRouter, z.AI and Gemini.

All four expose an OpenAI-style ``POST {base}/chat/completions`` with a Bearer key, so a
single client covers them; only the base URL, model and key differ.
"""

from __future__ import annotations

import httpx

from app.services.llm.base import LLMProvider, ProviderError, ProviderUnavailable


class OpenAICompatibleProvider(LLMProvider):
    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        model: str,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.extra_headers = extra_headers or {}

    def complete(self, system: str, user: str, *, timeout: float, json_mode: bool = True) -> str:
        if not self.api_key:
            raise ProviderUnavailable(f"{self.name}: no API key configured")

        payload: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.extra_headers,
        }

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=timeout,
            )
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.name}: transport error: {exc}") from exc

        if response.status_code >= 400:
            raise ProviderError(
                f"{self.name}: HTTP {response.status_code}: {response.text[:200]}"
            )

        try:
            return response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as exc:
            raise ProviderError(f"{self.name}: unexpected response shape: {exc}") from exc
