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

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env.local",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()