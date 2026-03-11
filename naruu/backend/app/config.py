"""NARUU Application Configuration.

Environment-based settings with validation.
All secrets loaded from environment variables.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "NARUU"
    APP_ENV: str = "development"
    APP_DEBUG: bool = False
    APP_PORT: int = 8000
    APP_LOG_LEVEL: str = "INFO"

    # Database (Railway PostgreSQL)
    DATABASE_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    # Claude API
    CLAUDE_API_KEY: Optional[str] = None
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # LINE Messaging API
    LINE_CHANNEL_ACCESS_TOKEN: Optional[str] = None
    LINE_CHANNEL_SECRET: Optional[str] = None

    # Google Maps
    GOOGLE_MAPS_API_KEY: Optional[str] = None

    # Make.com Webhooks
    MAKE_STORY_WEBHOOK_URL: Optional[str] = None
    MAKE_BROCHURE_WEBHOOK_URL: Optional[str] = None

    @property
    def async_database_url(self) -> str:
        """Convert postgres:// to postgresql+asyncpg://"""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
