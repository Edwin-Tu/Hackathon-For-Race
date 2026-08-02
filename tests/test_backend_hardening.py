"""Regression tests for backend-only cloud hardening.

These tests intentionally avoid static/UI files. They cover the integration
boundaries that must survive ECS restarts and multi-session polling.
"""

from __future__ import annotations

import time

import pytest

from app.output import OutputEnvelope, OutputEventStore
from app.repositories import InMemoryCareRepository
from app.tools.audit import RepositoryAuditStore
from app.tools.enums import RiskLevel, ToolStatus
from app.tools.gateway import ToolGateway
from app.tools.models import DemoAuthContextFactory, ToolCall
from app.tools.policy import ConfirmationStore


def _auth(*, requester_id: str = "user-1", session_id: str = "session-1"):
    return DemoAuthContextFactory.create_resident(
        requester_id=requester_id,
        persona_id="persona-1",
        session_id=session_id,
        request_id=f"request-{session_id}",
    )


def test_durable_confirmation_survives_store_recreation_and_is_single_use() -> None:
    repository = InMemoryCareRepository()
    first_store = ConfirmationStore(repository=repository)
    auth = _auth()
    tool_call = ToolCall(
        tool_call_id="tool-1",
        name="create_reminder",
        arguments={"title": "untrusted-client-value"},
    )
    validated_args = {
        "title": "回診",
        "scheduled_at": "2026-08-03T09:00:00+08:00",
        "importance": "high",
        "idempotency_key": "durable-confirmation-1",
    }

    token = first_store.create(
        request_id=auth.request_id,
        session_id=auth.session_id,
        requester_id=auth.requester_id,
        role=auth.role.value,
        tool_call=tool_call,
        validated_args=validated_args,
        target_persona_id=auth.active_persona_id,
        summary="建立回診提醒",
    )

    # A fresh store instance simulates a replacement ECS task.
    second_store = ConfirmationStore(repository=repository)
    pending, error = second_store.get_pending(token, auth)

    assert error == ""
    assert pending is not None
    assert pending.tool_call.arguments == validated_args
    assert second_store.consume(token, response_text="confirmed") is True
    assert second_store.consume(token, response_text="confirmed") is False


def test_durable_confirmation_remains_bound_to_requester_and_session() -> None:
    repository = InMemoryCareRepository()
    store = ConfirmationStore(repository=repository)
    owner = _auth(requester_id="owner", session_id="shared-session")
    attacker = _auth(requester_id="attacker", session_id="shared-session")
    token = store.create(
        request_id=owner.request_id,
        session_id=owner.session_id,
        requester_id=owner.requester_id,
        role=owner.role.value,
        tool_call=ToolCall(
            tool_call_id="tool-2",
            name="create_reminder",
            arguments={},
        ),
        validated_args={
            "title": "喝水",
            "scheduled_at": "2026-08-03T10:00:00+08:00",
            "importance": "normal",
            "idempotency_key": "durable-confirmation-2",
        },
        target_persona_id=owner.active_persona_id,
        summary="建立喝水提醒",
    )

    pending, error = ConfirmationStore(repository=repository).get_pending(
        token, attacker
    )

    assert pending is None
    assert "使用者" in error


def test_output_store_filters_persona_and_session_without_changing_ui_payload() -> None:
    store = OutputEventStore()
    store.append(
        OutputEnvelope(
            event_type="reminder.triggered",
            persona_id="persona-1",
            session_id="session-a",
            display_text="A",
            speech_text="A",
        )
    )
    store.append(
        OutputEnvelope(
            event_type="reminder.triggered",
            persona_id="persona-1",
            session_id="session-b",
            display_text="B",
            speech_text="B",
        )
    )
    store.append(
        OutputEnvelope(
            event_type="reminder.triggered",
            persona_id="persona-2",
            session_id="session-a",
            display_text="C",
            speech_text="C",
        )
    )

    visible = store.list(persona_ids={"persona-1"}, session_id="session-a")

    assert [event.display_text for event in visible] == ["A"]
    assert visible[0].to_dict()["session_id"] == "session-a"


def test_repository_audit_store_persists_only_argument_names() -> None:
    repository = InMemoryCareRepository()
    audit = RepositoryAuditStore(repository)
    auth = _auth()

    audit.log(
        auth_context=auth,
        tool_name="create_care_event",
        argument_names=["content", "source_text"],
        target_persona_id="persona-1",
        decision="allow",
        status=ToolStatus.SUCCEEDED,
        risk_level=RiskLevel.LOW,
        record_id="event-1",
    )

    rows = repository.get_all_audit_logs()
    assert len(rows) == 1
    assert rows[0]["argument_names"] == ["content", "source_text"]
    assert "照護內容" not in repr(rows[0])


def test_tool_timeout_returns_without_waiting_for_slow_worker() -> None:
    gateway = ToolGateway()

    def slow_handler(**_: object) -> dict[str, object]:
        time.sleep(0.25)
        return {"record_id": "late"}

    started = time.monotonic()
    with pytest.raises(TimeoutError):
        gateway._execute_with_timeout(
            handler=slow_handler,
            validated_args={},
            target_persona_id="persona-1",
            requester_id="user-1",
            timeout_seconds=0.02,
        )
    elapsed = time.monotonic() - started

    assert elapsed < 0.15


def test_turn_counter_is_bounded_for_long_running_ecs_process() -> None:
    gateway = ToolGateway()
    for index in range(4200):
        gateway._increment_turn_count(f"request-{index}")

    assert len(gateway._turn_tool_counts) == 4096
    assert "request-0" not in gateway._turn_tool_counts
    assert "request-4199" in gateway._turn_tool_counts
