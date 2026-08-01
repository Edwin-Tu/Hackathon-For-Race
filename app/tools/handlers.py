"""
Tool handlers with InMemoryCareRepository.

Handlers MUST NOT perform authorization - all permission checks
are done by Gateway before handler is called.

Handlers receive target_persona_id injected by Gateway,
NOT from model arguments.
"""

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo
from typing import Any

from app.tools.enums import get_event_type_display_name


@dataclass
class CareEvent:
    """A care event record."""

    record_id: str
    persona_id: str
    event_type: str
    content: str
    event_time: datetime
    confidence: float | None
    created_at: datetime
    created_by: str


@dataclass
class Reminder:
    """A reminder record."""

    record_id: str
    persona_id: str
    title: str
    scheduled_at: datetime
    importance: str
    created_at: datetime
    created_by: str


@dataclass
class ScheduleItem:
    """An item in user's schedule."""

    item_id: str
    item_type: str  # "reminder" or "event"
    title: str
    scheduled_time: datetime



class InMemoryCareRepository:
    """
    In-memory repository for care data.
    
    TODO: Replace with MySQL repository for production.
    """

    def __init__(self) -> None:
        self._events: dict[str, CareEvent] = {}
        self._reminders: dict[str, Reminder] = {}

    def create_care_event(
        self,
        persona_id: str,
        event_type: str,
        content: str,
        event_time: datetime,
        confidence: float | None,
        created_by: str,
    ) -> str:
        """Create a care event and return record_id."""
        record_id = str(uuid.uuid4())
        event = CareEvent(
            record_id=record_id,
            persona_id=persona_id,
            event_type=event_type,
            content=content,
            event_time=event_time,
            confidence=confidence,
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
        )
        self._events[record_id] = event
        return record_id

    def create_reminder(
        self,
        persona_id: str,
        title: str,
        scheduled_at: datetime,
        importance: str,
        created_by: str,
    ) -> str:
        """Create a reminder and return record_id."""
        record_id = str(uuid.uuid4())
        reminder = Reminder(
            record_id=record_id,
            persona_id=persona_id,
            title=title,
            scheduled_at=scheduled_at,
            importance=importance,
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
        )
        self._reminders[record_id] = reminder
        return record_id


    def get_user_schedule(
        self,
        persona_id: str,
        target_date: date | None = None,
    ) -> list[ScheduleItem]:
        """Get schedule items for a persona on a date."""
        if target_date is None:
            target_date = datetime.now(ZoneInfo("Asia/Taipei")).date()

        items: list[ScheduleItem] = []

        # Get reminders for the date
        for reminder in self._reminders.values():
            if reminder.persona_id != persona_id:
                continue
            if reminder.scheduled_at.date() == target_date:
                items.append(
                    ScheduleItem(
                        item_id=reminder.record_id,
                        item_type="reminder",
                        title=reminder.title,
                        scheduled_time=reminder.scheduled_at,
                    )
                )

        # Sort by time
        items.sort(key=lambda x: x.scheduled_time)
        return items

    def get_all_events(self) -> list[CareEvent]:
        """Get all events (for testing/demo)."""
        return list(self._events.values())

    def get_all_reminders(self) -> list[Reminder]:
        """Get all reminders (for testing/demo)."""
        return list(self._reminders.values())

    def clear(self) -> None:
        """Clear all data (for testing)."""
        self._events.clear()
        self._reminders.clear()



class ToolHandlers:
    """
    Handler implementations for registered tools.
    
    All handlers receive:
    - validated_args: Pydantic-validated arguments
    - target_persona_id: Injected by Gateway from AuthContext
    - requester_id: For audit trail
    """

    def __init__(self, repository: InMemoryCareRepository) -> None:
        self._repo = repository

    def handle_create_care_event(
        self,
        validated_args: dict[str, Any],
        target_persona_id: str,
        requester_id: str,
    ) -> dict[str, Any]:
        """Handle create_care_event tool call."""
        event_type = validated_args["event_type"]
        record_id = self._repo.create_care_event(
            persona_id=target_persona_id,
            event_type=event_type,
            content=validated_args["content"],
            event_time=validated_args["event_time"],
            confidence=validated_args.get("confidence"),
            created_by=requester_id,
        )
        display_name = get_event_type_display_name(event_type)
        return {
            "record_id": record_id,
            "message": f"已記錄{display_name}事件",
        }

    def handle_create_reminder(
        self,
        validated_args: dict[str, Any],
        target_persona_id: str,
        requester_id: str,
    ) -> dict[str, Any]:
        """Handle create_reminder tool call."""
        record_id = self._repo.create_reminder(
            persona_id=target_persona_id,
            title=validated_args["title"],
            scheduled_at=validated_args["scheduled_at"],
            importance=validated_args.get("importance", "normal"),
            created_by=requester_id,
        )
        return {
            "record_id": record_id,
            "message": f"已建立提醒：{validated_args['title']}",
        }

    def handle_get_user_schedule(
        self,
        validated_args: dict[str, Any],
        target_persona_id: str,
        requester_id: str,
    ) -> dict[str, Any]:
        """Handle get_user_schedule tool call."""
        date_str = validated_args.get("date")
        target_date = None
        if date_str:
            target_date = date.fromisoformat(date_str)

        items = self._repo.get_user_schedule(target_persona_id, target_date)

        if not items:
            return {
                "record_id": None,
                "message": "今天沒有安排的行程",
                "schedule": [],
            }

        schedule_list = [
            {
                "time": item.scheduled_time.strftime("%H:%M"),
                "type": item.item_type,
                "title": item.title,
            }
            for item in items
        ]
        return {
            "record_id": None,
            "message": f"找到 {len(items)} 個行程",
            "schedule": schedule_list,
        }
