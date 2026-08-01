"""Create a near-future reminder and wait for local scheduler delivery."""

from __future__ import annotations

import argparse
import asyncio
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import settings
from app.main import reminder_scheduler, repository

TAIPEI = ZoneInfo("Asia/Taipei")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", default="喝水")
    parser.add_argument("--delay-seconds", type=int, default=10)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    args = parser.parse_args()

    scheduled_at = datetime.now(TAIPEI) + timedelta(seconds=max(1, args.delay_seconds))
    reminder_id = repository.create_reminder(
        persona_id=settings.DEMO_PERSONA_ID,
        title=args.title,
        scheduled_at=scheduled_at,
        importance="normal",
        created_by=settings.DEMO_USER_ID,
        idempotency_key=f"scheduler-demo-{uuid.uuid4()}",
    )
    print(f"Created reminder_id={reminder_id}")
    print(f"Scheduled at {scheduled_at.isoformat()}")

    deadline = datetime.now(TAIPEI) + timedelta(seconds=args.timeout_seconds)
    while datetime.now(TAIPEI) < deadline:
        results = await reminder_scheduler.run_once()
        if any(result.reminder_id == reminder_id for result in results):
            for result in results:
                if result.reminder_id == reminder_id:
                    print(
                        f"Delivered status={result.status} "
                        f"backend={result.backend} error={result.error}"
                    )
                    return
        await asyncio.sleep(0.5)
    raise SystemExit("Reminder was not triggered before timeout")


if __name__ == "__main__":
    asyncio.run(main())
