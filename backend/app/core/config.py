from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "FHOS Core"
    app_version: str = "2.0.0"
    debug: bool = True

    api_prefix: str = "/api"

    database_url: str = "sqlite:///./fhos_local.db"

    secret_key: str = "local-secret-key"

    cors_origins: list[str] = ["*"]

    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-20250514"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash"

    ollama_base_url: str = "http://localhost:11434/api"
    ollama_model: str = "llama3.1"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env.local",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
