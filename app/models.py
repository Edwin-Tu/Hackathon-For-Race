"""Request and response models for the agent API."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """POST /api/agent/chat request body."""

    message: str = Field(..., min_length=1, description="使用者訊息")
    session_id: str | None = Field(None, description="可選的會話 ID")
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
    """GET /health response body."""

    status: str = "ok"
    app_env: str = ""
    model_id: str = ""
