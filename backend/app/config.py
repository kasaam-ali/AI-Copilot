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
    database_url: str = "sqlite:///./app.db"

    # LLM provider fallback chain, e.g. "groq,gemini,openrouter,zai,mock".
    llm_provider_order: str = "mock"

    @property
    def artifact_path(self) -> Path:
        return Path(self.artifact_root)

    @property
    def provider_order(self) -> list[str]:
        return [item.strip() for item in self.llm_provider_order.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
