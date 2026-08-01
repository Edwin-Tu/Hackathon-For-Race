from datetime import datetime, timedelta, timezone

import pytest

from app.output import DeliveryResult, OutputEnvelope
from app.reminders import ReminderScheduler
from app.repositories import InMemoryCareRepository

UTC = timezone.utc


class _RecordingAdapter:
    def __init__(self, *, ok: bool = True) -> None:
        self.ok = ok
        self.events: list[OutputEnvelope] = []

    def emit(self, envelope: OutputEnvelope) -> DeliveryResult:
        self.events.append(envelope)
        return DeliveryResult(
            ok=self.ok,
            backend="fake",
            error=None if self.ok else "delivery failed",
        )


@pytest.mark.asyncio
async def test_scheduler_claims_delivers_and_finalizes_once() -> None:
    repo = InMemoryCareRepository()
    adapter = _RecordingAdapter()
    now = datetime(2026, 8, 1, 6, 0, tzinfo=UTC)
    reminder_id = repo.create_reminder(
        persona_id="persona-1",
        title="喝水",
        scheduled_at=now - timedelta(seconds=5),
        importance="normal",
        created_by="user-1",
        idempotency_key="due-1",
    )
    scheduler = ReminderScheduler(
        repository=repo,
        output_adapter=adapter,
        missed_after_seconds=60,
    )

    first = await scheduler.run_once(now=now)
    second = await scheduler.run_once(now=now + timedelta(seconds=1))

    assert [item.status for item in first] == ["triggered"]
    assert second == []
    assert len(adapter.events) == 1
    assert adapter.events[0].source_id == reminder_id
    reminder = repo.get_all_reminders()[0]
    assert reminder.status == "triggered"
    assert reminder.triggered_at == now


@pytest.mark.asyncio
async def test_scheduler_does_not_claim_future_reminder() -> None:
    repo = InMemoryCareRepository()
    adapter = _RecordingAdapter()
    now = datetime(2026, 8, 1, 6, 0, tzinfo=UTC)
    repo.create_reminder(
        persona_id="persona-1",
        title="回診",
        scheduled_at=now + timedelta(minutes=5),
        importance="high",
        created_by="user-1",
        idempotency_key="future-1",
    )
    scheduler = ReminderScheduler(repository=repo, output_adapter=adapter)

    assert await scheduler.run_once(now=now) == []
    assert adapter.events == []
    assert repo.get_all_reminders()[0].status == "scheduled"


@pytest.mark.asyncio
async def test_scheduler_marks_old_reminder_missed_without_delivery() -> None:
    repo = InMemoryCareRepository()
    adapter = _RecordingAdapter()
    now = datetime(2026, 8, 1, 6, 0, tzinfo=UTC)
    repo.create_reminder(
        persona_id="persona-1",
        title="很久以前的提醒",
        scheduled_at=now - timedelta(hours=2),
        importance="normal",
        created_by="user-1",
        idempotency_key="old-1",
    )
    scheduler = ReminderScheduler(
        repository=repo,
        output_adapter=adapter,
        missed_after_seconds=60,
    )

    assert await scheduler.run_once(now=now) == []
    assert adapter.events == []
    assert repo.get_all_reminders()[0].status == "missed"


@pytest.mark.asyncio
async def test_scheduler_marks_failed_when_all_output_backends_fail() -> None:
    repo = InMemoryCareRepository()
    adapter = _RecordingAdapter(ok=False)
    now = datetime(2026, 8, 1, 6, 0, tzinfo=UTC)
    repo.create_reminder(
        persona_id="persona-1",
        title="吃藥",
        scheduled_at=now,
        importance="high",
        created_by="user-1",
        idempotency_key="fail-1",
    )
    scheduler = ReminderScheduler(repository=repo, output_adapter=adapter)

    results = await scheduler.run_once(now=now)

    assert results[0].status == "failed"
    assert repo.get_all_reminders()[0].status == "failed"
