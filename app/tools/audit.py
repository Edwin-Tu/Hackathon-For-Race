"""
Audit logging for tool operations.

Each preflight and execute creates an AuditEvent.

MUST NOT store:
- Argument values (only names)
- source_text content
- AWS credentials
- Full health records
- Stack traces
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Any

from app.tools.enums import RiskLevel, Role, ToolStatus
from app.tools.models import AuditEvent, AuthContext


class InMemoryAuditStore:
    """
    In-memory audit store.
    
    TODO: Replace with MySQL audit_logs table for production.
    """

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def log(
        self,
        auth_context: AuthContext,
        tool_name: str,
        argument_names: list[str],
        target_persona_id: str | None,
        decision: str,
        status: ToolStatus,
        risk_level: RiskLevel,
        requires_confirmation: bool = False,
        error_code: str | None = None,
        record_id: str | None = None,
        duration_ms: int | None = None,
    ) -> AuditEvent:
        """Create and store an audit event."""
        event = AuditEvent(
            audit_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            request_id=auth_context.request_id,
            session_id=auth_context.session_id,
            requester_id=auth_context.requester_id,
            role=auth_context.role,
            target_persona_id=target_persona_id,
            tool_name=tool_name,
            argument_names=argument_names,
            decision=decision,
            status=status,
            risk_level=risk_level,
            requires_confirmation=requires_confirmation,
            error_code=error_code,
            record_id=record_id,
            duration_ms=duration_ms,
        )
        self._events.append(event)
        return event

    def get_all(self) -> list[AuditEvent]:
        """Get all audit events (for testing/demo)."""
        return list(self._events)

    def get_by_request(self, request_id: str) -> list[AuditEvent]:
        """Get audit events for a specific request."""
        return [e for e in self._events if e.request_id == request_id]

    def get_by_session(self, session_id: str) -> list[AuditEvent]:
        """Get audit events for a session."""
        return [e for e in self._events if e.session_id == session_id]

    def clear(self) -> None:
        """Clear all events (for testing)."""
        self._events.clear()


def extract_argument_names(arguments: dict[str, Any]) -> list[str]:
    """
    Extract only argument names, not values.
    
    This ensures sensitive data like source_text content
    is never stored in audit logs.
    """
    return list(arguments.keys())
