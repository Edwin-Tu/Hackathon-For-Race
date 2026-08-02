"""Repository contracts shared by the Agent, Tool Gateway, and scheduler."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal, Protocol, runtime_checkable


class SessionScopeError(RuntimeError):
    """Raised when a session is accessed by another user or persona scope."""


@dataclass
class CareEvent:
    """A persisted care event."""

    record_id: str
    persona_id: str
    event_type: str
    content: str
    event_time: datetime
    confidence: float | None
    created_at: datetime
    created_by: str
    source_text: str | None = None
    idempotency_key: str | None = None


@dataclass
class Reminder:
    """A persisted reminder."""

    record_id: str
    persona_id: str
    title: str
    scheduled_at: datetime
    importance: str
    created_at: datetime
    created_by: str
    idempotency_key: str | None = None
    status: str = "scheduled"
    description: str | None = None
    triggered_at: datetime | None = None


@dataclass
class ScheduleItem:
    """A normalized schedule item returned to the Agent."""

    item_id: str
    item_type: str
    title: str
    scheduled_time: datetime


@dataclass(frozen=True)
class ConversationMessage:
    """One safe natural-language message loaded into Claude context."""

    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


@runtime_checkable
class CareRepository(Protocol):
    """Storage contract consumed by Agent, tools, and reminder scheduler."""

    def create_care_event(
        self,
        persona_id: str,
        event_type: str,
        content: str,
        event_time: datetime,
        confidence: float | None,
        created_by: str,
        source_text: str | None = None,
        idempotency_key: str | None = None,
    ) -> str: ...

    def create_reminder(
        self,
        persona_id: str,
        title: str,
        scheduled_at: datetime,
        importance: str,
        created_by: str,
        idempotency_key: str | None = None,
    ) -> str: ...

    def get_user_schedule(
        self,
        persona_id: str,
        target_date: date | None = None,
    ) -> list[ScheduleItem]: ...

    def claim_due_reminders(
        self,
        now: datetime,
        *,
        limit: int,
        missed_after_seconds: int,
    ) -> list[Reminder]: ...

    def mark_reminder_triggered(
        self,
        reminder_id: str,
        *,
        triggered_at: datetime,
    ) -> bool: ...

    def mark_reminder_failed(
        self,
        reminder_id: str,
        *,
        failed_at: datetime,
    ) -> bool: ...

    def recover_stale_reminders(
        self,
        *,
        stale_before: datetime,
    ) -> int: ...

    def ensure_conversation_session(
        self,
        *,
        session_id: str,
        user_id: str,
        persona_id: str,
    ) -> None: ...

    def append_conversation_turn(
        self,
        *,
        session_id: str,
        user_id: str,
        persona_id: str,
        request_id: str,
        user_message: str,
        assistant_message: str,
        input_type: str = "text",
    ) -> None: ...

    def list_recent_conversation_messages(
        self,
        *,
        session_id: str,
        user_id: str,
        persona_id: str,
        max_messages: int,
        max_chars: int,
    ) -> list[ConversationMessage]: ...
