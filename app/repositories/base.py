"""Repository contracts shared by the Tool Gateway handlers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol, runtime_checkable


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


@dataclass
class ScheduleItem:
    """A normalized schedule item returned to the Agent."""

    item_id: str
    item_type: str
    title: str
    scheduled_time: datetime


@runtime_checkable
class CareRepository(Protocol):
    """Storage contract consumed by ToolHandlers.

    The Tool Gateway remains storage agnostic. Implementations may persist to
    memory, MySQL, or another transactional store, but must preserve this
    contract.
    """

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
