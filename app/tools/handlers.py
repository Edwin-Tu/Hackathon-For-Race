"""Tool handlers that persist through a repository adapter.

Handlers MUST NOT perform authorization. Tool Gateway validates role, persona
scope, schema, confirmation, and turn limits before invoking these functions.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.repositories import (
    CareEvent,
    CareRepository,
    InMemoryCareRepository,
    Reminder,
    ScheduleItem,
)
from app.tools.enums import get_event_type_display_name

# Backward-compatible re-exports for existing tests/imports.
__all__ = [
    "CareEvent",
    "Reminder",
    "ScheduleItem",
    "InMemoryCareRepository",
    "ToolHandlers",
]


class ToolHandlers:
    """Repository-backed implementations for registered tools."""

    def __init__(self, repository: CareRepository) -> None:
        self._repo = repository

    def handle_create_care_event(
        self,
        validated_args: dict[str, Any],
        target_persona_id: str,
        requester_id: str,
    ) -> dict[str, Any]:
        event_type = validated_args["event_type"]
        record_id = self._repo.create_care_event(
            persona_id=target_persona_id,
            event_type=event_type,
            content=validated_args["content"],
            event_time=validated_args["event_time"],
            confidence=validated_args.get("confidence"),
            source_text=validated_args.get("source_text"),
            idempotency_key=validated_args.get("idempotency_key"),
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
        record_id = self._repo.create_reminder(
            persona_id=target_persona_id,
            title=validated_args["title"],
            scheduled_at=validated_args["scheduled_at"],
            importance=validated_args.get("importance", "normal"),
            idempotency_key=validated_args.get("idempotency_key"),
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
        del requester_id  # Query is already authorized by Tool Gateway.
        date_str = validated_args.get("date")
        target_date = date.fromisoformat(date_str) if date_str else None
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
