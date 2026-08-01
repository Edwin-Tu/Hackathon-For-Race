"""Regression tests for confirmation resume across text, voice, and UI flows."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app, agent_service as app_agent_service
from app.models import (
    ActionStatus,
    ChatRequest,
    ChatResponse,
    ConfirmationDecision,
    ConfirmationRequest,
    ProviderResponse,
    ToolUseBlock,
    UsageInfo,
)
from app.security import AgentInputGuard
from app.services.agent_service import AgentService
from app.tools import DemoAuthContextFactory, ToolCall, ToolGateway, ToolStatus


def _future_time() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()


def _reminder_provider_response(*, tool_use_id: str = "tool-reminder-confirm") -> ProviderResponse:
    tool_input = {
        "title": "回診",
        "scheduled_at": _future_time(),
        "importance": "normal",
        "idempotency_key": f"idem-{tool_use_id}",
    }
    return ProviderResponse(
        success=True,
        model="test-claude",
        stop_reason="tool_use",
        usage=UsageInfo(input_tokens=20, output_tokens=10, total_tokens=30),
        tool_use_blocks=[
            ToolUseBlock(
                tool_use_id=tool_use_id,
                name="create_reminder",
                input=tool_input,
            )
        ],
        raw_content=[
            {
                "toolUse": {
                    "toolUseId": tool_use_id,
                    "name": "create_reminder",
                    "input": tool_input,
                }
            }
        ],
    )


def _service() -> tuple[AgentService, AsyncMock, ToolGateway]:
    provider = MagicMock()
    provider.chat = AsyncMock(return_value=_reminder_provider_response())
    gateway = ToolGateway()
    service = AgentService(
        provider=provider,
        gateway=gateway,
        input_guard=AgentInputGuard(enabled=False, fail_closed=True),
    )
    return service, provider.chat, gateway


@pytest.mark.asyncio
async def test_plain_text_confirmation_resumes_without_token_or_bedrock() -> None:
    service, provider_chat, gateway = _service()

    first = await service.chat(
        ChatRequest(
            message="請提醒我一小時後回診",
            session_id="confirmation-text-session",
        )
    )
    assert first.requires_confirmation is True
    assert first.action_status == ActionStatus.CONFIRMATION_REQUIRED
    assert gateway.repository.get_all_reminders() == []

    second = await service.chat(
        ChatRequest(message="確認", session_id=first.session_id)
    )

    assert second.success is True
    assert second.operation_completed is True
    assert second.action_status == ActionStatus.COMPLETED
    assert second.usage.total_tokens == 0
    assert second.model == ""
    assert len(gateway.repository.get_all_reminders()) == 1
    assert provider_chat.await_count == 1  # confirmation itself never calls Bedrock


@pytest.mark.asyncio
async def test_plain_text_cancellation_consumes_pending_without_execution() -> None:
    service, provider_chat, gateway = _service()

    first = await service.chat(
        ChatRequest(
            message="請提醒我一小時後回診",
            session_id="confirmation-cancel-session",
        )
    )
    assert first.confirmation_token

    cancelled = await service.chat(
        ChatRequest(message="取消", session_id=first.session_id)
    )

    assert cancelled.success is True
    assert cancelled.action_status == ActionStatus.CANCELLED
    assert cancelled.operation_completed is False
    assert cancelled.tool_events[0].status == ToolStatus.CANCELLED.value
    assert gateway.repository.get_all_reminders() == []
    assert provider_chat.await_count == 1

    replay = await service.confirm(
        ConfirmationRequest(
            session_id=first.session_id,
            confirmation_token=first.confirmation_token,
            decision=ConfirmationDecision.CONFIRM,
        )
    )
    assert replay.success is False
    assert replay.error_type == "INVALID_CONFIRMATION"


@pytest.mark.asyncio
async def test_explicit_confirmation_endpoint_service_path() -> None:
    service, provider_chat, gateway = _service()
    first = await service.chat(
        ChatRequest(
            message="請提醒我一小時後回診",
            session_id="confirmation-endpoint-session",
        )
    )

    confirmed = await service.confirm(
        ConfirmationRequest(
            session_id=first.session_id,
            confirmation_token=first.confirmation_token,
            decision=ConfirmationDecision.CONFIRM,
        )
    )

    assert confirmed.success is True
    assert confirmed.operation_completed is True
    assert confirmed.tool_events[0].record_id
    assert len(gateway.repository.get_all_reminders()) == 1
    assert provider_chat.await_count == 1


@pytest.mark.asyncio
async def test_confirmation_words_without_pending_do_not_call_bedrock() -> None:
    service, provider_chat, _ = _service()

    response = await service.chat(
        ChatRequest(message="確認", session_id="no-pending-session")
    )

    assert response.success is False
    assert response.error_type == "NO_PENDING_CONFIRMATION"
    assert response.operation_completed is False
    assert provider_chat.await_count == 0


def test_confirmation_token_is_bound_to_requester() -> None:
    gateway = ToolGateway()
    original = DemoAuthContextFactory.create_resident(
        requester_id="resident-a",
        persona_id="persona-a",
        session_id="shared-session",
        request_id="request-a",
    )
    attacker = DemoAuthContextFactory.create_resident(
        requester_id="resident-b",
        persona_id="persona-a",
        session_id="shared-session",
        request_id="request-b",
    )
    pending = gateway.execute(
        ToolCall(
            tool_call_id="tool-requester-binding",
            name="create_reminder",
            arguments={
                "title": "回診",
                "scheduled_at": _future_time(),
                "importance": "normal",
                "idempotency_key": "idem-requester-binding",
            },
        ),
        original,
    )
    assert pending.confirmation_token

    denied = gateway.confirm_and_execute(pending.confirmation_token, attacker)

    assert denied.success is False
    assert denied.status == ToolStatus.DENIED
    assert denied.error_code == "INVALID_CONFIRMATION"
    assert "使用者" in denied.message


def test_confirm_api_route_is_available(monkeypatch: pytest.MonkeyPatch) -> None:
    mocked = AsyncMock(
        return_value=ChatResponse(
            success=True,
            reply="已建立提醒。",
            session_id="route-session",
            operation_completed=True,
            action_status=ActionStatus.COMPLETED,
        )
    )
    monkeypatch.setattr(app_agent_service, "confirm", mocked)

    with TestClient(app) as client:
        response = client.post(
            "/api/agent/confirm",
            json={
                "session_id": "route-session",
                "confirmation_token": "opaque-token",
                "decision": "confirm",
            },
        )

    assert response.status_code == 200
    assert response.json()["operation_completed"] is True
    mocked.assert_awaited_once()
