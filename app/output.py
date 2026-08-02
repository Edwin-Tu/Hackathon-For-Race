"""Transport-neutral output events and adapters.

The reminder scheduler emits OutputEnvelope objects. UI, local speech, console,
or future WebSocket adapters can consume the same envelope without changing the
scheduler or Tool Gateway.
"""

from __future__ import annotations

import logging
import threading
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OutputEnvelope:
    """A reminder or agent output ready for one or more delivery backends."""

    event_type: str
    persona_id: str
    display_text: str
    speech_text: str
    source_id: str | None = None
    session_id: str | None = None
    event_id: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data


@dataclass(frozen=True)
class DeliveryResult:
    """Result returned by an OutputAdapter."""

    ok: bool
    backend: str
    error: str | None = None


class OutputAdapter(Protocol):
    """Output delivery contract."""

    def emit(self, envelope: OutputEnvelope) -> DeliveryResult: ...


class ConsoleOutputAdapter:
    """Always-available text output used for logs and demos."""

    backend = "console"

    def emit(self, envelope: OutputEnvelope) -> DeliveryResult:
        logger.info(
            "Output event: type=%s source_id=%s persona_id=%s text=%s",
            envelope.event_type,
            envelope.source_id,
            envelope.persona_id,
            envelope.display_text,
        )
        print(f"[REMINDER] {envelope.display_text}", flush=True)
        return DeliveryResult(ok=True, backend=self.backend)


class NullOutputAdapter:
    """Explicitly discard output while still marking delivery as handled."""

    backend = "null"

    def emit(self, envelope: OutputEnvelope) -> DeliveryResult:
        del envelope
        return DeliveryResult(ok=True, backend=self.backend)


class OutputEventStore:
    """Thread-safe bounded in-memory queue for a future UI/WebSocket adapter."""

    def __init__(self, max_events: int = 200) -> None:
        self._events: deque[OutputEnvelope] = deque(maxlen=max(1, max_events))
        self._next_id = 1
        self._lock = threading.Lock()

    def append(self, envelope: OutputEnvelope) -> OutputEnvelope:
        with self._lock:
            stored = OutputEnvelope(
                event_type=envelope.event_type,
                persona_id=envelope.persona_id,
                display_text=envelope.display_text,
                speech_text=envelope.speech_text,
                source_id=envelope.source_id,
                session_id=envelope.session_id,
                event_id=self._next_id,
                metadata=dict(envelope.metadata),
                created_at=envelope.created_at,
            )
            self._next_id += 1
            self._events.append(stored)
            return stored

    def list(
        self,
        *,
        after_id: int | None = None,
        limit: int = 50,
        persona_ids: set[str] | None = None,
        session_id: str | None = None,
    ) -> list[OutputEnvelope]:
        with self._lock:
            events = list(self._events)
        if after_id is not None:
            events = [event for event in events if (event.event_id or 0) > after_id]
        if persona_ids is not None:
            events = [event for event in events if event.persona_id in persona_ids]
        if session_id is not None:
            events = [event for event in events if event.session_id == session_id]
        return events[-max(1, min(limit, 200)) :]

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


class StoreOutputAdapter:
    """Persist output in OutputEventStore for later polling by a UI."""

    backend = "event_store"

    def __init__(self, store: OutputEventStore) -> None:
        self._store = store

    def emit(self, envelope: OutputEnvelope) -> DeliveryResult:
        self._store.append(envelope)
        return DeliveryResult(ok=True, backend=self.backend)


class CompositeOutputAdapter:
    """Fan out to multiple adapters while isolating individual failures.

    Delivery is considered successful when at least one backend succeeds. This
    ensures an unavailable audio backend does not discard an otherwise visible
    console/event-store reminder.
    """

    def __init__(self, *adapters: OutputAdapter) -> None:
        self._adapters = tuple(adapters)

    def emit(self, envelope: OutputEnvelope) -> DeliveryResult:
        if not self._adapters:
            return DeliveryResult(ok=False, backend="none", error="No output adapters")

        results: list[DeliveryResult] = []
        for adapter in self._adapters:
            try:
                results.append(adapter.emit(envelope))
            except Exception as exc:  # pragma: no cover - defensive boundary
                logger.exception("Output adapter failed: %s", type(adapter).__name__)
                results.append(
                    DeliveryResult(
                        ok=False,
                        backend=type(adapter).__name__,
                        error=str(exc),
                    )
                )

        successful = [result for result in results if result.ok]
        errors = [
            f"{result.backend}: {result.error or 'failed'}"
            for result in results
            if not result.ok
        ]
        return DeliveryResult(
            ok=bool(successful),
            backend="+".join(result.backend for result in results),
            error="; ".join(errors) if errors else None,
        )
