"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    AWS_REGION: str = "us-west-2"
    AWS_PROFILE: str | None = None
    BEDROCK_MODEL_ID: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Persistence: memory | mysql | auto
    CARE_REPOSITORY_BACKEND: str = "auto"
    DATABASE_URL: str | None = None
    DATABASE_PING_ON_STARTUP: bool = True

    # Development identity. Production must replace this with JWT/session auth.
    DEMO_USER_ID: str = "demo-user"
    DEMO_PERSONA_ID: str = "demo-persona"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
