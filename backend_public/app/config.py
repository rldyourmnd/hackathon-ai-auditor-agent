from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8080, alias="APP_PORT")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    app_secret: str = Field(default="change_me_super_secret", alias="APP_SECRET")
    cors_origins: List[str] = Field(default_factory=list, alias="CORS_ORIGINS")

    database_url: str = Field(alias="DATABASE_URL")

    google_client_id: str = Field(default="", alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", alias="GOOGLE_CLIENT_SECRET")
    google_oauth_redirect: str = Field(
        default="http://localhost:8080/auth/google/callback", alias="GOOGLE_OAUTH_REDIRECT"
    )

    jwt_issuer: str = Field(default="auditor.public", alias="JWT_ISSUER")
    jwt_expire_minutes: int = Field(default=120, alias="JWT_EXPIRE_MINUTES")

    # Internal pipeline API base (for Swagger/OpenAPI and proxy)
    internal_api_base: str = Field(default="http://api:8000", alias="INTERNAL_API_BASE")
    http_timeout_seconds: int = Field(default=30, alias="HTTP_TIMEOUT_SECONDS")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v


settings = Settings()  # reads env
