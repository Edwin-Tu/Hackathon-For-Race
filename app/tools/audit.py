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
import logging
from datetime import datetime, timezone
from typing import Any

from app.repositories import CareRepository
from app.tools.enums import RiskLevel, Role, ToolStatus
from app.tools.models import AuditEvent, AuthContext

logger = logging.getLogger(__name__)


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


class RepositoryAuditStore(InMemoryAuditStore):
    """Keep the test/debug view while durably appending sanitized audit rows."""

    def __init__(self, repository: CareRepository) -> None:
        super().__init__()
        self._repository = repository

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
        event = super().log(
            auth_context=auth_context,
            tool_name=tool_name,
            argument_names=argument_names,
            target_persona_id=target_persona_id,
            decision=decision,
            status=status,
            risk_level=risk_level,
            requires_confirmation=requires_confirmation,
            error_code=error_code,
            record_id=record_id,
            duration_ms=duration_ms,
        )
        try:
            self._repository.append_audit_log(
                audit_id=event.audit_id,
                timestamp=event.timestamp,
                request_id=event.request_id,
                session_id=event.session_id,
                requester_id=event.requester_id,
                role=event.role.value,
                target_persona_id=event.target_persona_id,
                tool_name=event.tool_name,
                argument_names=event.argument_names,
                decision=event.decision,
                status=event.status.value,
                risk_level=event.risk_level.value,
                requires_confirmation=event.requires_confirmation,
                error_code=event.error_code,
                record_id=event.record_id,
                duration_ms=event.duration_ms,
            )
        except Exception:
            # Tool safety decisions must remain available even if the audit
            # database is temporarily unavailable. The failure is visible in
            # application logs without including protected argument values.
            logger.exception(
                "Durable audit append failed request_id=%s tool=%s",
                event.request_id,
                event.tool_name,
            )
        return event


def extract_argument_names(arguments: dict[str, Any]) -> list[str]:
    """
    Extract only argument names, not values.
    
    This ensures sensitive data like source_text content
    is never stored in audit logs.
    """
    return list(arguments.keys())
