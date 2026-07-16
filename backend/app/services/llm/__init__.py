"""Provider-agnostic LLM layer with a deterministic offline fallback.

The deep-learning models make every prediction; this layer only narrates them. It never
raises to the caller: the fallback chain always terminates in a deterministic mock, so the
product works fully offline and demos never depend on a live API key.
"""

from app.services.llm.chain import FallbackLLMService, get_llm_service

__all__ = ["FallbackLLMService", "get_llm_service"]
