"""Request and response models for the agent API."""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ConfirmationDecision(str, Enum):
    """User decision for a pending server-side tool operation."""

    CONFIRM = "confirm"
    CANCEL = "cancel"


class ConfirmationRequest(BaseModel):
    """POST /api/agent/confirm request body."""

    session_id: str = Field(..., min_length=1, description="原始工作階段 ID")
    confirmation_token: str = Field(..., min_length=1, description="伺服器簽發的單次確認代碼")
    decision: ConfirmationDecision = Field(
        ConfirmationDecision.CONFIRM,
        description="confirm 或 cancel",
    )


class ChatRequest(BaseModel):
    """POST /api/agent/chat request body."""

    message: str = Field(..., min_length=1, description="使用者訊息")
    session_id: str | None = Field(None, min_length=1, max_length=191, description="可選的會話 ID")
    input_type: Literal["text", "voice"] = Field(
        "text", description="訊息來源；由後端語音端點設定為 voice"
    )
    # For confirming pending tool operations
    confirmation_token: str | None = Field(None, description="工具確認代碼")


class UsageInfo(BaseModel):
    """Token usage information."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class ToolUseBlock(BaseModel):
    """A tool use request from the model."""

    tool_use_id: str
    name: str
    input: dict[str, Any]


class ActionStatus(str, Enum):
    """Status of the action requested by user."""

    NO_ACTION = "no_action"  # No tool action needed (e.g., simple chat)
    CLARIFICATION_REQUIRED = "clarification_required"  # Need more info from user
    CONFIRMATION_REQUIRED = "confirmation_required"  # Awaiting user confirmation
    COMPLETED = "completed"  # Write tool executed successfully
    QUERY_COMPLETED = "query_completed"  # Read-only query executed successfully
    DENIED = "denied"  # Tool execution was denied (auth/validation)
    CANCELLED = "cancelled"  # User cancelled a pending operation
    FAILED = "failed"  # Tool execution failed


class ToolEvent(BaseModel):
    """
    Summary of a tool execution event.
    
    DOES NOT include:
    - Full arguments
    - source_text
    - confirmation token
    - AWS credentials
    - Internal auth data
    """

    tool_call_id: str = Field(..., description="Tool call ID")
    tool_name: str = Field(..., description="Name of the tool")
    status: str = Field(..., description="Tool status (succeeded, failed, denied, etc.)")
    success: bool = Field(..., description="Whether the tool succeeded")
    record_id: str | None = Field(None, description="Created record ID if any")
    error_code: str | None = Field(None, description="Error code if failed")
    idempotency_replayed: bool = Field(False, description="Whether replayed via idempotency")


class InputGuardEvidence(BaseModel):
    """Minimized Input Guard evidence safe for API clients and audit UI."""

    enabled: bool = True
    allowed: bool = False
    action: str = "BLOCK"
    overall_risk_level: str = "unknown"
    overall_risk_score: int = 0
    attack_risk_score: int = 0
    access_risk_score: int = 0
    primary_category: str = "none"
    is_attack: bool = False
    is_suspicious: bool = False
    strict_runtime_monitoring: bool = False
    reason_codes: list[str] = Field(default_factory=list)


class InputGuardCheckRequest(BaseModel):
    """Development endpoint request for inspecting text without invoking Bedrock."""

    message: str = Field(..., min_length=1, description="Text to inspect")
    session_id: str | None = Field(None, description="Optional session ID")


class InputGuardCheckResponse(BaseModel):
    """Safe direct Input Guard inspection response."""

    request_id: str
    session_id: str
    allowed: bool
    action: str
    sanitized_text: str | None = None
    safe_response: str | None = None
    input_guard: InputGuardEvidence


class ChatResponse(BaseModel):
    """POST /api/agent/chat response body."""

    success: bool
    reply: str = ""
    model: str = ""
    session_id: str = ""
    usage: UsageInfo = UsageInfo()
    error_type: str | None = None
    error_message: str | None = None
    # For tool confirmation flow
    requires_confirmation: bool = False
    confirmation_token: str | None = None
    confirmation_summary: str | None = None
    # Tool execution evidence for frontend
    operation_completed: bool = Field(
        False,
        description="True only if tool executed with status=succeeded and success=true",
    )
    action_status: ActionStatus = Field(
        ActionStatus.NO_ACTION,
        description="Status of the requested action",
    )
    tool_events: list[ToolEvent] = Field(
        default_factory=list,
        description="List of tool execution events (no sensitive data)",
    )
    input_guard: InputGuardEvidence | None = Field(
        None,
        description="Minimized pre-LLM Input Guard decision evidence",
    )


class ProviderResponse(BaseModel):
    """Unified response from any LLM provider."""

    success: bool
    text: str = ""
    model: str = ""
    stop_reason: str = ""
    usage: UsageInfo = UsageInfo()
    error_type: str | None = None
    error_message: str | None = None
    # For tool use
    tool_use_blocks: list[ToolUseBlock] = Field(default_factory=list)
    raw_content: list[dict[str, Any]] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """GET /health response body (never contains secret values)."""

    status: str = "ok"
    app_env: str = ""
    model_id: str = ""
    api_auth_required: bool = False
    repository_backend: str = ""
    event_table: str = ""


class TranscriptionTrace(BaseModel):
    """Whisper metadata safe to expose to an API client."""

    model: str
    language: str | None = None
    language_probability: float | None = None
    duration_seconds: float | None = None
    duration_after_vad_seconds: float | None = None
    segment_count: int = 0


class TranscriptionResponse(BaseModel):
    """POST /api/voice/transcribe response."""

    transcript: str
    trace: TranscriptionTrace


class SpeechDeliveryTrace(BaseModel):
    """Local speech delivery result for a voice turn."""

    ok: bool
    backend: str
    error: str | None = None


class VoiceTurnResponse(BaseModel):
    """POST /api/voice/turn response."""

    transcript: str
    trace: TranscriptionTrace
    agent: ChatResponse
    speech_delivery: SpeechDeliveryTrace | None = None


class ReminderRunItem(BaseModel):
    reminder_id: str
    status: str
    backend: str | None = None
    error: str | None = None


class ReminderRunResponse(BaseModel):
    processed: int
    results: list[ReminderRunItem] = Field(default_factory=list)


class OutputEventResponse(BaseModel):
    event_type: str
    persona_id: str
    display_text: str
    speech_text: str
    source_id: str | None = None
    session_id: str | None = None
    event_id: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str
