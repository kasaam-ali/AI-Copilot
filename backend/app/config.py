"""Application configuration loaded from the environment / .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings. Values come from environment variables or backend/.env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SentinelQ"
    app_api_key: str = "change-me"
    artifact_root: str = "./artifacts"
    report_root: str = "./reports"
    database_url: str = "sqlite:///./app.db"

    # LLM provider fallback chain, e.g. "groq,openrouter,zai,gemini,mock".
    llm_provider_order: str = "mock"
    llm_timeout_seconds: float = 8.0

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai"

    openrouter_api_key: str = ""
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    zai_api_key: str = ""
    zai_model: str = "glm-4.5-flash"
    zai_base_url: str = "https://api.z.ai/api/paas/v4"

    @property
    def artifact_path(self) -> Path:
        return Path(self.artifact_root)

    @property
    def report_path(self) -> Path:
        return Path(self.report_root)

    @property
    def provider_order(self) -> list[str]:
        return [item.strip() for item in self.llm_provider_order.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
