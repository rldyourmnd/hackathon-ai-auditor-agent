from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Literal


class Settings(BaseSettings):
    # Align with backend/app/core/config.py pattern
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # General
    env: Literal["development", "production"] = Field(default="development", alias="ENV")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO", alias="LOG_LEVEL")

    # App
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8080, alias="APP_PORT")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    app_secret: str = Field(default="change_me_super_secret", alias="APP_SECRET")
    cors_origins: List[str] = Field(default_factory=list, alias="CORS_ORIGINS")
    admin_emails: List[str] = Field(default_factory=list, alias="ADMIN_EMAILS")

    # Database (default asyncpg per rebase guideline)
    database_url: str = Field(
        default="postgresql+asyncpg://curestry:secure_password@db:5432/curestry",
        alias="DATABASE_URL",
    )
    # Optional Redis for caching/ratelimiting
    redis_url: str | None = Field(default=None, alias="REDIS_URL")

    # OAuth
    google_client_id: str = Field(default="", alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", alias="GOOGLE_CLIENT_SECRET")
    google_oauth_redirect: str = Field(
        default="http://localhost:8080/auth/google/callback", alias="GOOGLE_OAUTH_REDIRECT"
    )

    # JWT
    jwt_issuer: str = Field(default="auditor.public", alias="JWT_ISSUER")
    jwt_expire_minutes: int = Field(default=120, alias="JWT_EXPIRE_MINUTES")

    # Internal pipeline API base (for Swagger/OpenAPI and proxy)
    internal_api_base: str = Field(default="http://api:8000", alias="INTERNAL_API_BASE")
    http_timeout_seconds: int = Field(default=30, alias="HTTP_TIMEOUT_SECONDS")

    # Feature flags (service continuity / gradual rollout)
    feature_proxy: bool = Field(default=True, alias="FEATURE_PROXY")
    feature_internal_proxy: bool = Field(default=True, alias="FEATURE_INTERNAL_PROXY")
    feature_metrics: bool = Field(default=True, alias="FEATURE_METRICS")
    feature_workflow_api: bool = Field(default=True, alias="FEATURE_WORKFLOW_API")
    feature_auth: bool = Field(default=True, alias="FEATURE_AUTH")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @field_validator("admin_emails", mode="before")
    @classmethod
    def split_admins(cls, v):
        if isinstance(v, str):
            return [s.strip().lower() for s in v.split(",") if s.strip()]
        return [s.strip().lower() for s in v]


settings = Settings()  # reads env
