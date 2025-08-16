from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable loading."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # General settings
    env: Literal["development", "production"] = Field(default="development")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")

    # Database settings
    postgres_user: str = Field(default="curestry")
    postgres_password: str = Field(default="secure_password")
    postgres_db: str = Field(default="curestry")
    database_url: str = Field(
        default="postgresql+psycopg://curestry:secure_password@db:5432/curestry"
    )

    # Redis settings
    redis_url: str = Field(default="redis://redis:6379/0")

    # OpenAI settings
    openai_api_key: str = Field(default="", description="OpenAI API key (optional for demo)", alias="OPENAI_API_KEY")
    openai_model_cheap: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL_CHEAP")
    openai_model_standard: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL_STANDARD")
    openai_model_premium: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL_PREMIUM")

    # Analysis configuration
    entropy_n: int = Field(default=8, description="Number of samples for semantic entropy")

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.env == "production"


# Global settings instance
settings = Settings()
