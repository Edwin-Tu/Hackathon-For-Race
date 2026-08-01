"""In-memory repository used by unit tests and local fallback mode."""

from __future__ import annotations

import threading
import uuid
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from app.repositories.base import CareEvent, Reminder, ScheduleItem


class InMemoryCareRepository:
    """Process-local repository. Data is lost when the server restarts."""

    def __init__(self) -> None:
        self._events: dict[str, CareEvent] = {}
        self._reminders: dict[str, Reminder] = {}
        self._event_idempotency: dict[tuple[str, str], str] = {}
        self._reminder_idempotency: dict[tuple[str, str], str] = {}
        self._lock = threading.RLock()

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
    ) -> str:
        with self._lock:
            if idempotency_key:
                existing = self._event_idempotency.get((persona_id, idempotency_key))
                if existing:
                    return existing

            record_id = str(uuid.uuid4())
            event = CareEvent(
                record_id=record_id,
                persona_id=persona_id,
                event_type=event_type,
                content=content,
                event_time=event_time,
                confidence=confidence,
                source_text=source_text,
                idempotency_key=idempotency_key,
                created_at=datetime.now(timezone.utc),
                created_by=created_by,
            )
            self._events[record_id] = event
            if idempotency_key:
                self._event_idempotency[(persona_id, idempotency_key)] = record_id
            return record_id

    def create_reminder(
        self,
        persona_id: str,
        title: str,
        scheduled_at: datetime,
        importance: str,
        created_by: str,
        idempotency_key: str | None = None,
    ) -> str:
        with self._lock:
            if idempotency_key:
                existing = self._reminder_idempotency.get((persona_id, idempotency_key))
                if existing:
                    return existing

            record_id = str(uuid.uuid4())
            reminder = Reminder(
                record_id=record_id,
                persona_id=persona_id,
                title=title,
                scheduled_at=scheduled_at,
                importance=importance,
                idempotency_key=idempotency_key,
                created_at=datetime.now(timezone.utc),
                created_by=created_by,
                status="scheduled",
            )
            self._reminders[record_id] = reminder
            if idempotency_key:
                self._reminder_idempotency[(persona_id, idempotency_key)] = record_id
            return record_id

    def get_user_schedule(
        self,
        persona_id: str,
        target_date: date | None = None,
    ) -> list[ScheduleItem]:
        if target_date is None:
            target_date = datetime.now(ZoneInfo("Asia/Taipei")).date()

        with self._lock:
            items: list[ScheduleItem] = []
            for reminder in self._reminders.values():
                if reminder.persona_id != persona_id:
                    continue
                if reminder.status not in {"scheduled", "triggering"}:
                    continue
                if reminder.scheduled_at.astimezone(ZoneInfo("Asia/Taipei")).date() == target_date:
                    items.append(
                        ScheduleItem(
                            item_id=reminder.record_id,
                            item_type="reminder",
                            title=reminder.title,
                            scheduled_time=reminder.scheduled_at,
                        )
                    )
            items.sort(key=lambda item: item.scheduled_time)
            return items

    def claim_due_reminders(
        self,
        now: datetime,
        *,
        limit: int,
        missed_after_seconds: int,
    ) -> list[Reminder]:
        if now.tzinfo is None:
            raise ValueError("now must include timezone information")

        claimed: list[Reminder] = []
        with self._lock:
            candidates = sorted(
                (
                    reminder
                    for reminder in self._reminders.values()
                    if reminder.status == "scheduled" and reminder.scheduled_at <= now
                ),
                key=lambda reminder: reminder.scheduled_at,
            )
            for reminder in candidates[:limit]:
                overdue_seconds = max(
                    0.0,
                    (now - reminder.scheduled_at).total_seconds(),
                )
                if overdue_seconds > missed_after_seconds:
                    reminder.status = "missed"
                    continue
                reminder.status = "triggering"
                claimed.append(reminder)
        return list(claimed)

    def mark_reminder_triggered(
        self,
        reminder_id: str,
        *,
        triggered_at: datetime,
    ) -> bool:
        with self._lock:
            reminder = self._reminders.get(reminder_id)
            if reminder is None or reminder.status != "triggering":
                return False
            reminder.status = "triggered"
            reminder.triggered_at = triggered_at
            return True

    def mark_reminder_failed(
        self,
        reminder_id: str,
        *,
        failed_at: datetime,
    ) -> bool:
        del failed_at
        with self._lock:
            reminder = self._reminders.get(reminder_id)
            if reminder is None or reminder.status != "triggering":
                return False
            reminder.status = "failed"
            return True

    def recover_stale_reminders(
        self,
        *,
        stale_before: datetime,
    ) -> int:
        del stale_before
        recovered = 0
        with self._lock:
            for reminder in self._reminders.values():
                if reminder.status == "triggering":
                    reminder.status = "scheduled"
                    recovered += 1
        return recovered

    def get_all_events(self) -> list[CareEvent]:
        with self._lock:
            return list(self._events.values())

    def get_all_reminders(self) -> list[Reminder]:
        with self._lock:
            return list(self._reminders.values())

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
            self._reminders.clear()
            self._event_idempotency.clear()
            self._reminder_idempotency.clear()
