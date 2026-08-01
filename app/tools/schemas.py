"""
Pydantic schemas for tool arguments.

All schemas use extra="forbid" to prevent Claude from injecting
unauthorized fields like persona_id, resident_id, or SQL.
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.tools.enums import EventType, Importance


class CreateCareEventArgs(BaseModel):
    """
    Arguments for create_care_event tool.
    
    Model MUST NOT provide:
    - persona_id
    - resident_id
    - role
    - requester_id
    - authorized_persona_ids
    - SQL
    - table_name
    """

    event_type: EventType = Field(..., description="Type of care event")
    content: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Event content/description",
    )
    event_time: datetime = Field(
        ...,
        description="Event time in ISO 8601 with timezone (prefer Asia/Taipei)",
    )
    confidence: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Optional confidence score from speech recognition",
    )
    source_text: str | None = Field(
        None,
        max_length=500,
        description="Optional original user utterance",
    )
    idempotency_key: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Idempotency key for deduplication",
    )

    model_config = {"extra": "forbid"}

    @field_validator("event_time")
    @classmethod
    def validate_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("event_time must include timezone information")
        return v


class CreateReminderArgs(BaseModel):
    """
    Arguments for create_reminder tool.
    
    Model MUST NOT provide persona_id or resident_id.
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Reminder title",
    )
    scheduled_at: datetime = Field(
        ...,
        description="Scheduled time in ISO 8601 with timezone",
    )
    importance: Importance = Field(
        Importance.NORMAL,
        description="Importance level: low, normal, high",
    )
    source_text: str | None = Field(
        None,
        max_length=500,
        description="Optional original user utterance",
    )
    idempotency_key: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Idempotency key for deduplication",
    )

    model_config = {"extra": "forbid"}

    @field_validator("scheduled_at")
    @classmethod
    def validate_future_time(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("scheduled_at must include timezone information")
        # Note: In production, should check if time is in the future
        # For demo, we allow any time with timezone
        return v


class GetUserScheduleArgs(BaseModel):
    """
    Arguments for get_user_schedule tool.
    
    Model MUST NOT provide persona_id.
    Backend injects target persona from AuthContext.
    """

    date: str | None = Field(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Date in YYYY-MM-DD format (optional, defaults to today)",
    )

    model_config = {"extra": "forbid"}


# Bedrock tool configuration schemas (for model visibility)
TOOL_SCHEMAS = {
    "create_care_event": {
        "name": "create_care_event",
        "description": "只用於新增或保存已發生的照護事件。當使用者說記錄、記下、保存、已完成、已吃藥、已散步、已用餐或已睡眠時使用。不得用於查詢既有行程。",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "event_type": {
                        "type": "string",
                        "enum": [e.value for e in EventType],
                        "description": "事件類型",
                    },
                    "content": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 1000,
                        "description": "事件內容描述",
                    },
                    "event_time": {
                        "type": "string",
                        "format": "date-time",
                        "description": "事件時間，ISO 8601 格式並包含時區",
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "語音辨識信心度（可選）",
                    },
                    "source_text": {
                        "type": "string",
                        "maxLength": 500,
                        "description": "使用者原始語句（可選）",
                    },
                    "idempotency_key": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 64,
                        "description": "冪等鍵，避免重複建立",
                    },
                },
                "required": ["event_type", "content", "event_time", "idempotency_key"],
                "additionalProperties": False,
            }
        },
    },
    "create_reminder": {
        "name": "create_reminder",
        "description": "只用於建立未來提醒。當使用者說提醒我、幫我提醒、建立提醒或設定提醒時使用。不得用於記錄已發生事件或查詢行程。",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 200,
                        "description": "提醒標題",
                    },
                    "scheduled_at": {
                        "type": "string",
                        "format": "date-time",
                        "description": "提醒時間，ISO 8601 格式並包含時區",
                    },
                    "importance": {
                        "type": "string",
                        "enum": [i.value for i in Importance],
                        "description": "重要程度：low、normal、high",
                    },
                    "source_text": {
                        "type": "string",
                        "maxLength": 500,
                        "description": "使用者原始語句（可選）",
                    },
                    "idempotency_key": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 64,
                        "description": "冪等鍵，避免重複建立",
                    },
                },
                "required": ["title", "scheduled_at", "idempotency_key"],
                "additionalProperties": False,
            }
        },
    },
    "get_user_schedule": {
        "name": "get_user_schedule",
        "description": "只用於查看或查詢既有行程、提醒與預約。不得用於新增、記錄或保存已發生的事件。",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
                        "description": "查詢日期，格式 YYYY-MM-DD（可選，預設為今天）",
                    },
                },
                "required": [],
                "additionalProperties": False,
            }
        },
    },
}
