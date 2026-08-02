"""In-memory repository used by unit tests and local fallback mode."""

from __future__ import annotations

import threading
import uuid
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from app.repositories.base import (
    CareEvent,
    ConversationMessage,
    PendingToolConfirmation,
    Reminder,
    ScheduleItem,
    SessionScopeError,
)


class InMemoryCareRepository:
    """Process-local repository. Data is lost when the server restarts."""

    def __init__(self) -> None:
        self._events: dict[str, CareEvent] = {}
        self._reminders: dict[str, Reminder] = {}
        self._event_idempotency: dict[tuple[str, str], str] = {}
        self._reminder_idempotency: dict[tuple[str, str], str] = {}
        self._conversation_sessions: dict[str, tuple[str, str]] = {}
        self._conversation_messages: list[tuple[str, str, str, ConversationMessage]] = []
        self._pending_confirmations: dict[str, PendingToolConfirmation] = {}
        self._audit_logs: list[dict[str, object]] = []
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


    def ensure_conversation_session(
        self,
        *,
        session_id: str,
        user_id: str,
        persona_id: str,
    ) -> None:
        """Create or validate a session bound to one trusted user/persona scope."""
        with self._lock:
            existing = self._conversation_sessions.get(session_id)
            scope = (user_id, persona_id)
            if existing is not None and existing != scope:
                raise SessionScopeError(
                    "session_id belongs to a different user or persona"
                )
            self._conversation_sessions[session_id] = scope

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
    ) -> None:
        del request_id, input_type
        self.ensure_conversation_session(
            session_id=session_id,
            user_id=user_id,
            persona_id=persona_id,
        )
        now = datetime.now(timezone.utc)
        with self._lock:
            if user_message.strip():
                self._conversation_messages.append((
                    session_id,
                    user_id,
                    persona_id,
                    ConversationMessage(
                        role="user",
                        content=user_message.strip(),
                        created_at=now,
                    ),
                ))
            if assistant_message.strip():
                self._conversation_messages.append((
                    session_id,
                    user_id,
                    persona_id,
                    ConversationMessage(
                        role="assistant",
                        content=assistant_message.strip(),
                        created_at=now,
                    ),
                ))

    def list_recent_conversation_messages(
        self,
        *,
        session_id: str,
        user_id: str,
        persona_id: str,
        max_messages: int,
        max_chars: int,
    ) -> list[ConversationMessage]:
        self.ensure_conversation_session(
            session_id=session_id,
            user_id=user_id,
            persona_id=persona_id,
        )
        with self._lock:
            matching = [
                message
                for sid, uid, pid, message in self._conversation_messages
                if sid == session_id and uid == user_id and pid == persona_id
            ]
        selected: list[ConversationMessage] = []
        chars = 0
        for message in reversed(matching):
            if len(selected) >= max(0, max_messages):
                break
            size = len(message.content)
            if selected and chars + size > max_chars:
                break
            if not selected and size > max_chars:
                message = ConversationMessage(
                    role=message.role,
                    content=message.content[-max_chars:],
                    created_at=message.created_at,
                )
                size = len(message.content)
            selected.append(message)
            chars += size
        return list(reversed(selected))

    def create_pending_confirmation(
        self,
        confirmation: PendingToolConfirmation,
    ) -> None:
        with self._lock:
            for token_hash, existing in list(self._pending_confirmations.items()):
                if (
                    not existing.consumed
                    and existing.session_id == confirmation.session_id
                    and existing.requester_id == confirmation.requester_id
                ):
                    del self._pending_confirmations[token_hash]
            self._pending_confirmations[confirmation.token_hash] = confirmation

    def get_pending_confirmation(
        self,
        *,
        token_hash: str,
    ) -> PendingToolConfirmation | None:
        with self._lock:
            return self._pending_confirmations.get(token_hash)

    def get_pending_confirmation_for_context(
        self,
        *,
        session_id: str,
        requester_id: str,
        role: str,
    ) -> list[PendingToolConfirmation]:
        with self._lock:
            return [
                item
                for item in self._pending_confirmations.values()
                if not item.consumed
                and item.session_id == session_id
                and item.requester_id == requester_id
                and item.role == role
            ]

    def consume_pending_confirmation(
        self,
        *,
        token_hash: str,
        response_text: str,
    ) -> bool:
        del response_text
        with self._lock:
            item = self._pending_confirmations.get(token_hash)
            if item is None or item.consumed:
                return False
            del self._pending_confirmations[token_hash]
            return True

    def append_audit_log(
        self,
        *,
        audit_id: str,
        timestamp: datetime,
        request_id: str,
        session_id: str,
        requester_id: str,
        role: str,
        target_persona_id: str | None,
        tool_name: str,
        argument_names: list[str],
        decision: str,
        status: str,
        risk_level: str,
        requires_confirmation: bool,
        error_code: str | None,
        record_id: str | None,
        duration_ms: int | None,
    ) -> None:
        with self._lock:
            self._audit_logs.append({
                "audit_id": audit_id,
                "timestamp": timestamp,
                "request_id": request_id,
                "session_id": session_id,
                "requester_id": requester_id,
                "role": role,
                "target_persona_id": target_persona_id,
                "tool_name": tool_name,
                "argument_names": list(argument_names),
                "decision": decision,
                "status": status,
                "risk_level": risk_level,
                "requires_confirmation": requires_confirmation,
                "error_code": error_code,
                "record_id": record_id,
                "duration_ms": duration_ms,
            })

    def get_all_audit_logs(self) -> list[dict[str, object]]:
        with self._lock:
            return list(self._audit_logs)

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
            self._conversation_sessions.clear()
            self._conversation_messages.clear()
            self._pending_confirmations.clear()
            self._audit_logs.clear()
