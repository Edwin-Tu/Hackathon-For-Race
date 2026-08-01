"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    AWS_REGION: str = "us-west-2"
    AWS_PROFILE: str | None = None
    BEDROCK_MODEL_ID: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
