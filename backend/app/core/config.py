from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration."""

    app_name: str = Field(
        default="Email Bomb Detection Platform",
        alias="APP_NAME",
    )

    app_version: str = Field(
        default="1.0.0",
        alias="APP_VERSION",
    )

    app_env: str = Field(
        default="development",
        alias="APP_ENV",
    )

    debug: bool = Field(
        default=True,
        alias="DEBUG",
    )

    api_v1_prefix: str = Field(
        default="/api/v1",
        alias="API_V1_PREFIX",
    )

    database_url: str = Field(
        default="sqlite:///./email_bomb_detection.db",
        alias="DATABASE_URL",
    )

    jwt_secret_key: str = Field(
        default="CHANGE_THIS_IN_PRODUCTION",
        alias="JWT_SECRET_KEY",
    )

    jwt_algorithm: str = Field(
        default="HS256",
        alias="JWT_ALGORITHM",
    )

    access_token_expire_minutes: int = Field(
        default=1440,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
        ge=1,
    )

    cors_origins: str = Field(
        default="http://localhost:8000,http://localhost:5173",
        alias="CORS_ORIGINS",
    )

    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Reject development-only security settings outside dev/test."""
        environment = self.app_env.strip().lower()
        if environment not in {"development", "dev", "test", "testing"}:
            if self.debug:
                raise ValueError("DEBUG must be false outside development and test environments.")
            if (
                self.jwt_secret_key == "CHANGE_THIS_IN_PRODUCTION"
                or len(self.jwt_secret_key.encode("utf-8")) < 32
            ):
                raise ValueError(
                    "JWT_SECRET_KEY must be a unique secret of at least 32 bytes outside development and test environments."
                )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def cors_origin_list(self) -> list[str]:
        """Return configured CORS origins."""
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton settings object."""
    return Settings()


settings = get_settings()
