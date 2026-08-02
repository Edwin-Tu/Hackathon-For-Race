"""Repository adapters."""

from app.repositories.base import (
    CareEvent,
    CareRepository,
    ConversationMessage,
    PendingToolConfirmation,
    Reminder,
    ScheduleItem,
    SessionScopeError,
)
from app.repositories.factory import create_care_repository
from app.repositories.memory import InMemoryCareRepository

__all__ = [
    "CareEvent",
    "CareRepository",
    "ConversationMessage",
    "PendingToolConfirmation",
    "InMemoryCareRepository",
    "Reminder",
    "ScheduleItem",
    "SessionScopeError",
    "create_care_repository",
]
