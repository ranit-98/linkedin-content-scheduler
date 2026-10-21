from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "LinkedIn Post Scheduler"
    app_env: str = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/linkedin_scheduler"
    redis_url: str = "redis://localhost:6379/0"
    frontend_url: str = "http://localhost:3000"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_redirect_uri: str = "http://localhost:8000/api/v1/auth/linkedin/callback"
    linkedin_api_version: str = "202609"
    linkedin_mock_mode: bool = False

    token_encryption_key: str = ""
    scheduler_interval_seconds: int = 15
    oauth_state_ttl_minutes: int = 10
    publish_timeout_seconds: float = 20.0
    retry_base_delay_seconds: int = 60
    retry_max_delay_seconds: int = 3600
    processing_timeout_minutes: int = 10

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: object) -> object:
        if isinstance(value, str) and not value.startswith("["):
            return [item.strip() for item in value.split(",")]
        return value

    def validate_secrets(self) -> None:
        if not self.token_encryption_key:
            raise RuntimeError("TOKEN_ENCRYPTION_KEY is required")
        if not self.linkedin_mock_mode and (
            not self.linkedin_client_id or not self.linkedin_client_secret
        ):
            raise RuntimeError(
                "LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET are required outside mock mode"
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
