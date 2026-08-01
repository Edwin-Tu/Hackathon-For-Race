"""Write/read smoke test for the persistent Agent repository."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import settings
from app.repositories.mysql import MySQLCareRepository


def main() -> None:
    if not settings.DATABASE_URL:
        raise SystemExit("DATABASE_URL is not configured")

    repo = MySQLCareRepository(settings.DATABASE_URL)
    now = datetime.now(ZoneInfo("Asia/Taipei"))

    event_id = repo.create_care_event(
        persona_id=settings.DEMO_PERSONA_ID,
        event_type="activity",
        content="資料庫整合檢查：散步十分鐘",
        event_time=now,
        confidence=1.0,
        source_text="資料庫整合檢查",
        idempotency_key=f"db-check-event-{uuid.uuid4()}",
        created_by=settings.DEMO_USER_ID,
    )

    reminder_time = now + timedelta(minutes=30)
    reminder_id = repo.create_reminder(
        persona_id=settings.DEMO_PERSONA_ID,
        title="資料庫整合檢查提醒",
        scheduled_at=reminder_time,
        importance="normal",
        idempotency_key=f"db-check-reminder-{uuid.uuid4()}",
        created_by=settings.DEMO_USER_ID,
    )

    schedule = repo.get_user_schedule(
        settings.DEMO_PERSONA_ID,
        reminder_time.date(),
    )

    print(f"[PASS] care_event record_id={event_id}")
    print(f"[PASS] reminder record_id={reminder_id}")
    print(f"[PASS] schedule_count={len(schedule)}")


if __name__ == "__main__":
    main()
