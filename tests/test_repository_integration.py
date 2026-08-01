"""Repository contract tests used by Agent ToolHandlers."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.repositories import InMemoryCareRepository
from app.tools.handlers import ToolHandlers

TZ = ZoneInfo("Asia/Taipei")


def test_care_event_handler_persists_source_and_idempotency() -> None:
    repo = InMemoryCareRepository()
    handlers = ToolHandlers(repo)
    args = {
        "event_type": "activity",
        "content": "散步二十分鐘",
        "event_time": datetime(2026, 8, 1, 16, 0, tzinfo=TZ),
        "confidence": 0.98,
        "source_text": "我今天下午四點散步二十分鐘",
        "idempotency_key": "event-001",
    }

    first = handlers.handle_create_care_event(args, "persona-1", "user-1")
    second = handlers.handle_create_care_event(args, "persona-1", "user-1")

    assert first["record_id"] == second["record_id"]
    events = repo.get_all_events()
    assert len(events) == 1
    assert events[0].source_text == args["source_text"]
    assert events[0].idempotency_key == "event-001"


def test_reminder_handler_is_idempotent_and_queryable() -> None:
    repo = InMemoryCareRepository()
    handlers = ToolHandlers(repo)
    args = {
        "title": "喝水",
        "scheduled_at": datetime(2026, 8, 1, 17, 30, tzinfo=TZ),
        "importance": "normal",
        "source_text": "下午五點半提醒我喝水",
        "idempotency_key": "reminder-001",
    }

    first = handlers.handle_create_reminder(args, "persona-1", "user-1")
    second = handlers.handle_create_reminder(args, "persona-1", "user-1")
    result = handlers.handle_get_user_schedule(
        {"date": "2026-08-01"}, "persona-1", "user-1"
    )

    assert first["record_id"] == second["record_id"]
    assert len(repo.get_all_reminders()) == 1
    assert result["record_id"] is None
    assert result["schedule"] == [
        {"time": "17:30", "type": "reminder", "title": "喝水"}
    ]


def test_schedule_isolated_by_persona() -> None:
    repo = InMemoryCareRepository()
    repo.create_reminder(
        persona_id="persona-a",
        title="A",
        scheduled_at=datetime(2026, 8, 1, 10, 0, tzinfo=TZ),
        importance="normal",
        created_by="user-a",
        idempotency_key="a-1",
    )
    repo.create_reminder(
        persona_id="persona-b",
        title="B",
        scheduled_at=datetime(2026, 8, 1, 11, 0, tzinfo=TZ),
        importance="normal",
        created_by="user-b",
        idempotency_key="b-1",
    )

    items = repo.get_user_schedule("persona-a", date(2026, 8, 1))
    assert [item.title for item in items] == ["A"]
