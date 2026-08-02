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

    # Bilingual voice input. Explicit zh-TW requests use faster-whisper and
    # explicit nan-TW requests use Breeze-ASR-26. Auto mode uses the configured
    # primary and only falls back after an unavailable/empty result.
    ASR_MODE: str = "hybrid"
    ASR_AUTO_PRIMARY: str = "whisper"
    ASR_FALLBACK_ENABLED: bool = True
    WHISPER_ENABLED: bool = True
    WHISPER_MODEL_SIZE: str = "small"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"
    WHISPER_DOWNLOAD_ROOT: str | None = None
    WHISPER_BEAM_SIZE: int = 5
    WHISPER_VAD_FILTER: bool = True
    BREEZE_ASR_ENABLED: bool = False
    BREEZE_ASR_MODEL_ID: str = "MediaTek-Research/Breeze-ASR-26"
    BREEZE_ASR_DEVICE: str = "auto"
    MAX_AUDIO_BYTES: int = 15 * 1024 * 1024

    # Taiwanese reply path: translate the complete Agent reply, then synthesize
    # the translated romanized text with the optional Min Nan TTS model.
    TAIWANESE_REPLY_TRANSLATION_ENABLED: bool = True
    TAIWANESE_TTS_ENABLED: bool = False
    TAIWANESE_TTS_MODEL_ID: str = "facebook/mms-tts-nan"
    TAIWANESE_TTS_DEVICE: str = "auto"
    TAIWANESE_TTS_MAX_CHARS: int = 600
    MAX_TTS_AUDIO_BYTES: int = 5 * 1024 * 1024

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
