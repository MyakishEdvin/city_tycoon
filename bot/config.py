"""
Centralized, typed configuration for the whole project.

Every process (the bot, and later the FastAPI backend) imports `settings`
from here instead of calling `os.getenv` directly. This keeps configuration
in one place and gives us validation errors at startup instead of at
runtime deep inside some handler.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Telegram ---
    BOT_TOKEN: str

    # --- Database ---
    DATABASE_URL: str

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Mini App ---
    WEBAPP_URL: str = ""

    # --- Security ---
    SECRET_KEY: str = "insecure-dev-secret-change-me"

    # --- Environment ---
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def webapp_configured(self) -> bool:
        return bool(self.WEBAPP_URL)


settings = Settings()  # type: ignore[call-arg]
