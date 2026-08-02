"""Application configuration using pydantic-settings.

The same application can run locally or in an AWS container service. Sensitive values
must be supplied through environment variables or an AWS secret reference;
no credentials are embedded in source code.
"""

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    AWS_REGION: str = "us-west-2"
    AWS_PROFILE: str | None = None
    BEDROCK_MODEL_ID: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Deterministic pre-LLM Input Guard.
    INPUT_GUARD_ENABLED: bool = True
    INPUT_GUARD_FAIL_CLOSED: bool = True

    # Durable conversation context. History is scoped to the trusted
    # user_id + persona_id + session_id tuple and re-sent to Bedrock.
    CONVERSATION_HISTORY_ENABLED: bool = True
    CONVERSATION_HISTORY_MAX_MESSAGES: int = 12
    CONVERSATION_HISTORY_MAX_CHARS: int = 12000

    # Minimal access control for a public cloud demo endpoint. Production must
    # replace this with Cognito/JWT; the bearer token is intentionally never
    # included in API responses or logs.
    API_AUTH_ENABLED: bool = False
    API_BEARER_TOKEN: SecretStr | None = None

    # Persistence: memory | mysql | auto.
    CARE_REPOSITORY_BACKEND: str = "auto"
    DATABASE_URL: SecretStr | None = None
    DATABASE_PING_ON_STARTUP: bool = True
    # auto supports both the locally verified `events` table and Edwin's RDS
    # `care_events` table without destructive schema changes.
    CARE_EVENT_TABLE: str = "auto"
    # preferred | required | verify_ca | verify_identity | disabled
    DATABASE_SSL_MODE: str = "preferred"
    DATABASE_SSL_CA: str | None = None

    # Voice input (faster-whisper). In the cloud the model can be preloaded in
    # the container image to avoid downloading it during service startup.
    WHISPER_ENABLED: bool = True
    WHISPER_MODEL_SIZE: str = "small"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"
    WHISPER_DOWNLOAD_ROOT: str | None = None
    WHISPER_BEAM_SIZE: int = 5
    WHISPER_VAD_FILTER: bool = True
    MAX_AUDIO_BYTES: int = 15 * 1024 * 1024

    # Reminder scheduler and output.
    REMINDER_SCHEDULER_ENABLED: bool = True
    REMINDER_POLL_SECONDS: float = 2.0
    REMINDER_BATCH_SIZE: int = 20
    REMINDER_MISSED_AFTER_SECONDS: int = 3600
    REMINDER_STALE_CLAIM_SECONDS: int = 120
    OUTPUT_EVENT_BUFFER_SIZE: int = 200
    LOCAL_ALARM_ENABLED: bool = True
    LOCAL_ALARM_SOUND_FILE: str | None = None
    LOCAL_TTS_ENABLED: bool = True
    VOICE_TURN_LOCAL_TTS_ENABLED: bool = True
    LOCAL_TTS_VOICE: str | None = None
    LOCAL_TTS_RATE: int | None = None

    # Development identity. Production must replace this with JWT/session auth.
    DEMO_USER_ID: str = "demo-user"
    DEMO_PERSONA_ID: str = "demo-persona"

    model_config = {"env_file": ".env", "extra": "ignore"}

    def database_url_value(self) -> str | None:
        """Return DATABASE_URL without exposing it through repr/logging."""
        return self.DATABASE_URL.get_secret_value() if self.DATABASE_URL else None

    def api_bearer_token_value(self) -> str | None:
        """Return the configured demo token for constant-time comparison."""
        return self.API_BEARER_TOKEN.get_secret_value() if self.API_BEARER_TOKEN else None


settings = Settings()
