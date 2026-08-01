"""Fixed enumerations for Tool Gateway."""

from enum import Enum


class Role(str, Enum):
    """User roles in the eldercare system."""

    RESIDENT = "resident"
    CAREGIVER = "caregiver"
    FAMILY = "family"
    ADMIN = "admin"
    SYSTEM = "system"


class EventType(str, Enum):
    """Types of care events."""

    MEAL = "meal"
    ACTIVITY = "activity"
    SLEEP = "sleep"
    MEDICATION = "medication"
    APPOINTMENT = "appointment"
    MOOD = "mood"
    FAMILY_CONTACT = "family_contact"
    GENERAL = "general"

    @property
    def display_name(self) -> str:
        """Return Chinese display name for the event type."""
        return EVENT_TYPE_DISPLAY_NAMES.get(self, self.value)


# Chinese display names for event types
EVENT_TYPE_DISPLAY_NAMES: dict["EventType", str] = {
    EventType.MEAL: "飲食",
    EventType.ACTIVITY: "活動",
    EventType.SLEEP: "睡眠",
    EventType.MEDICATION: "用藥",
    EventType.APPOINTMENT: "預約",
    EventType.MOOD: "情緒",
    EventType.FAMILY_CONTACT: "家人聯繫",
    EventType.GENERAL: "一般",
}


def get_event_type_display_name(event_type: str | EventType) -> str:
    """Get Chinese display name for event type."""
    if isinstance(event_type, EventType):
        return event_type.display_name
    try:
        return EventType(event_type).display_name
    except ValueError:
        return event_type


class ToolStatus(str, Enum):
    """Tool execution status."""

    PROPOSED = "proposed"
    VALIDATED = "validated"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DENIED = "denied"


class RiskLevel(str, Enum):
    """Risk level for tool operations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Importance(str, Enum):
    """Importance level for reminders."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
