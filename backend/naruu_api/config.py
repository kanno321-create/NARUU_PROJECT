"""
NARUU Tourism Platform - API Configuration
Environment variable loading with validation and safe defaults
"""

import os
from dotenv import load_dotenv

load_dotenv()


class ConfigError(Exception):
    """Configuration validation error"""
    pass


class Config:
    """Application configuration with environment variable validation"""

    # Database
    DATABASE_URL: str = ""

    # Application
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    APP_DEBUG: bool = False
    APP_LOG_LEVEL: str = "INFO"
    APP_VERSION: str = "0.1.0"

    # Database pool
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    # Redis (optional)
    REDIS_URL: str = ""
    REDIS_TTL: int = 3600

    # JWT Auth
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # LINE Messaging API
    LINE_CHANNEL_ACCESS_TOKEN: str = ""
    LINE_CHANNEL_SECRET: str = ""

    # Claude AI
    ANTHROPIC_API_KEY: str = ""

    # Translation
    DEEPL_API_KEY: str = ""

    # Currency
    EXCHANGE_RATE_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: str = ""

    def __init__(self):
        self._load_required_env_vars()
        self._load_optional_env_vars()
        self._validate_config()

    def _load_required_env_vars(self) -> None:
        required_vars = {
            "DATABASE_URL": "PostgreSQL connection URL",
            "JWT_SECRET_KEY": "JWT signing secret",
        }
        missing = []
        for var_name, desc in required_vars.items():
            value = os.getenv(var_name)
            if not value:
                missing.append(f"{var_name} ({desc})")
            else:
                setattr(self, var_name, value)

        if missing:
            raise ConfigError(
                "Missing required environment variables:\n"
                + "\n".join(f"  - {v}" for v in missing)
            )

    def _load_optional_env_vars(self) -> None:
        self.APP_ENV = os.getenv("APP_ENV", self.APP_ENV)
        self.APP_PORT = int(os.getenv("APP_PORT", str(self.APP_PORT)))
        self.APP_DEBUG = os.getenv("APP_DEBUG", "false").lower() in ("true", "1")
        self.APP_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", self.APP_LOG_LEVEL)

        self.DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", str(self.DB_POOL_SIZE)))
        self.DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", str(self.DB_MAX_OVERFLOW)))
        self.DB_ECHO = os.getenv("DB_ECHO", "false").lower() in ("true", "1")

        self.REDIS_URL = os.getenv("REDIS_URL", "")
        self.REDIS_TTL = int(os.getenv("REDIS_TTL", str(self.REDIS_TTL)))

        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", self.JWT_ALGORITHM)
        self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
            os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", str(self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
        )

        self.LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
        self.LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
        self.DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", "")
        self.EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY", "")
        self.CORS_ORIGINS = os.getenv("CORS_ORIGINS", "")

    def _validate_config(self) -> None:
        if not self.DATABASE_URL.startswith("postgres"):
            raise ConfigError("DATABASE_URL must start with postgres:// or postgresql://")
        if len(self.JWT_SECRET_KEY) < 16:
            raise ConfigError("JWT_SECRET_KEY must be at least 16 characters")

    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    def is_development(self) -> bool:
        return self.APP_ENV.lower() == "development"


try:
    config = Config()
except ConfigError as e:
    import sys
    print(f"Configuration Error: {e}")
    print("Please ensure all required environment variables are set.")
    sys.exit(1)
