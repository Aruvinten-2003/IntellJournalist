"""Application configuration loaded from environment variables and `.env`."""

from pathlib import Path
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Validated runtime settings for the Intell Journalist API."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Intell Journalist API"
    app_version: str = "0.1.0"
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = True
    host: str = "127.0.0.1"
    port: int = 5500
    api_prefix: str = "/api"
    log_level: str = "INFO"

    mongodb_url: str = "mongodb://127.0.0.1:27017"
    mongodb_database: str = "intell_journalist"
    mongodb_connect_timeout_ms: int = 5000
    database_required: bool = False

    jwt_secret_key: SecretStr = SecretStr("development-only-change-this-secret")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4o-mini"
    news_api_key: SecretStr | None = None

    cors_origins: list[str] = [
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ]

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """Reject known development secrets in production."""
        if (
            self.environment == "production"
            and self.jwt_secret_key.get_secret_value()
            == "development-only-change-this-secret"
        ):
            raise ValueError("JWT_SECRET_KEY must be changed before production use")
        return self

    @property
    def frontend_directory(self) -> Path:
        return PROJECT_ROOT / "frontend"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
