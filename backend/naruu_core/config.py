"""설정 관리 — 환경변수 및 플러그인 설정."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class NaruuSettings(BaseSettings):
    """NARUU 플랫폼 설정."""

    app_name: str = "NARUU AI Platform"
    app_version: str = "0.1.0"
    debug: bool = False

    # API
    api_prefix: str = "/v1"
    cors_origins: list[str] = ["http://localhost:3000"]

    # AI
    anthropic_api_key: str = ""

    # DB
    database_url: str = ""
    db_echo: bool = False

    # JWT
    jwt_secret: str = ""
    jwt_expire_minutes: int = 60

    # 플러그인
    plugin_dir: str = "naruu_core/plugins"
    auto_discover_plugins: bool = True

    model_config = {"env_prefix": "NARUU_", "env_file": ".env"}


def get_settings() -> NaruuSettings:
    """설정 싱글턴."""
    return NaruuSettings()
