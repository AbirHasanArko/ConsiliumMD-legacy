"""Application-wide configuration loaded from environment."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    database_url: str = "sqlite:///./consilium.db"

    jwt_secret: str = "change-me-in-prod"
    jwt_alg: str = "HS256"
    jwt_access_ttl_min: int = 60
    jwt_refresh_ttl_min: int = 1440

    reasoning_provider: Literal["mock", "carma"] = "mock"
    carma_base_url: str = "http://carma:8100"
    carma_api_key: str = ""
    carma_timeout_s: float = 15.0

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    log_level: str = "INFO"
    seed_demo_data: bool = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
