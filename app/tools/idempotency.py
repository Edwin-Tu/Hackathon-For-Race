"""
Idempotency control for write operations.

All write tools must have idempotency_key.
Scope: session_id + tool_name + target_persona_id + idempotency_key

When same key is resubmitted:
- Do not create new record
- Return original ToolResult
- Set idempotency_replayed = True

Read tools do not require idempotency_key.
"""

import time
from dataclasses import dataclass
from typing import Any

from app.tools.models import ToolResult


@dataclass
class IdempotencyRecord:
    """Stored record for idempotency checking."""

    key: str
    tool_result: ToolResult
    created_at: float
    expires_at: float


class InMemoryIdempotencyStore:
    """
    In-memory idempotency store.
    
    TODO: Replace with MySQL repository for production.
    Interface designed to be swappable.
    """

    DEFAULT_TTL_SECONDS = 3600  # 1 hour

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self._store: dict[str, IdempotencyRecord] = {}
        self._ttl_seconds = ttl_seconds

    def _make_key(
        self,
        session_id: str,
        tool_name: str,
        target_persona_id: str | None,
        idempotency_key: str,
    ) -> str:
        """Create composite key for idempotency lookup."""
        persona = target_persona_id or "_none_"
        return f"{session_id}:{tool_name}:{persona}:{idempotency_key}"

    def get(
        self,
        session_id: str,
        tool_name: str,
        target_persona_id: str | None,
        idempotency_key: str,
    ) -> ToolResult | None:
        """
        Check if idempotency key exists and return original result.
        
        Returns None if not found or expired.
        """
        self._cleanup_expired()
        key = self._make_key(session_id, tool_name, target_persona_id, idempotency_key)
        record = self._store.get(key)
        if record is None:
            return None
        if time.time() > record.expires_at:
            del self._store[key]
            return None
        return record.tool_result

    def store(
        self,
        session_id: str,
        tool_name: str,
        target_persona_id: str | None,
        idempotency_key: str,
        tool_result: ToolResult,
    ) -> None:
        """Store tool result for idempotency checking."""
        key = self._make_key(session_id, tool_name, target_persona_id, idempotency_key)
        now = time.time()
        self._store[key] = IdempotencyRecord(
            key=key,
            tool_result=tool_result,
            created_at=now,
            expires_at=now + self._ttl_seconds,
        )

    def _cleanup_expired(self) -> None:
        """Remove expired records."""
        now = time.time()
        expired = [k for k, v in self._store.items() if now > v.expires_at]
        for k in expired:
            del self._store[k]

    def clear(self) -> None:
        """Clear all stored records (for testing)."""
        self._store.clear()
