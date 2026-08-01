"""Regression tests for deterministic intent routing and completion evidence."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from app.models import ChatRequest, ProviderResponse, ToolUseBlock, UsageInfo
from app.services.agent_service import AgentService
from app.services.intent_router import RequestedAction, classify_intent
from app.tools import ToolGateway


def future_time() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()


class RecordingProvider:
    """Small async provider stub that records every call."""

    def __init__(self, responses: list[ProviderResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[dict] = []

    async def chat(self, messages, system_prompt, tool_config=None):
        self.calls.append(
            {
                "messages": messages,
                "system_prompt": system_prompt,
                "tool_config": tool_config,
            }
        )
        return self.responses.pop(0)


def make_response(
    *,
    text: str = "",
    stop_reason: str = "end_turn",
    tools: list[ToolUseBlock] | None = None,
    raw_content: list[dict] | None = None,
) -> ProviderResponse:
    return ProviderResponse(
        success=True,
        text=text,
        model="test-model",
        stop_reason=stop_reason,
        usage=UsageInfo(input_tokens=1, output_tokens=1, total_tokens=2),
        tool_use_blocks=tools or [],
        raw_content=raw_content or ([{"text": text}] if text else []),
    )


def test_router_selects_write_tool_for_explicit_record_request():
    decision = classify_intent("請幫我記錄：我今天下午四點散步二十分鐘。")
    assert decision.action == RequestedAction.CREATE_CARE_EVENT
    assert decision.expected_tool == "create_care_event"
    assert decision.force_tool is True


def test_router_does_not_force_ambiguous_period():
    decision = classify_intent("請幫我記錄：我今天下午散步二十分鐘。")
    assert decision.expected_tool == "create_care_event"
    assert decision.force_tool is False


@pytest.mark.asyncio
async def test_write_intent_exposes_and_forces_only_create_care_event():
    provider = RecordingProvider([make_response(text="請補充時間")])
    service = AgentService(provider=provider, gateway=ToolGateway())

    await service.chat(
        ChatRequest(
            message="請幫我記錄：我今天下午四點散步二十分鐘。",
            session_id="s-routing",
        )
    )

    config = provider.calls[0]["tool_config"]
    names = [item["toolSpec"]["name"] for item in config["tools"]]
    assert names == ["create_care_event"]
    assert config["toolChoice"] == {
        "tool": {"name": "create_care_event"}
    }


@pytest.mark.asyncio
async def test_write_intent_rejects_read_tool_mismatch_without_execution():
    tool = ToolUseBlock(
        tool_use_id="wrong-tool",
        name="get_user_schedule",
        input={},
    )
    provider = RecordingProvider(
        [
            make_response(
                stop_reason="tool_use",
                tools=[tool],
                raw_content=[
                    {
                        "toolUse": {
                            "toolUseId": "wrong-tool",
                            "name": "get_user_schedule",
                            "input": {},
                        }
                    }
                ],
            )
        ]
    )
    gateway = ToolGateway()
    service = AgentService(provider=provider, gateway=gateway)

    response = await service.chat(
        ChatRequest(
            message="請幫我記錄：我今天下午四點散步二十分鐘。",
            session_id="s-mismatch",
        )
    )

    assert response.operation_completed is False
    assert response.action_status.value == "failed"
    assert response.error_type == "TOOL_INTENT_MISMATCH"
    assert response.tool_events[0].tool_name == "get_user_schedule"
    assert response.tool_events[0].error_code == "TOOL_INTENT_MISMATCH"
    assert gateway.repository.get_all_events() == []


@pytest.mark.asyncio
async def test_read_tool_success_is_query_completed_not_write_completed():
    tool = ToolUseBlock(
        tool_use_id="schedule-tool",
        name="get_user_schedule",
        input={},
    )
    provider = RecordingProvider(
        [
            make_response(
                stop_reason="tool_use",
                tools=[tool],
                raw_content=[
                    {
                        "toolUse": {
                            "toolUseId": "schedule-tool",
                            "name": "get_user_schedule",
                            "input": {},
                        }
                    }
                ],
            ),
            make_response(text="今天沒有安排的行程。"),
        ]
    )
    service = AgentService(provider=provider, gateway=ToolGateway())

    response = await service.chat(
        ChatRequest(message="今天有什麼行程？", session_id="s-query")
    )

    assert response.operation_completed is False
    assert response.action_status.value == "query_completed"
    assert response.tool_events[0].tool_name == "get_user_schedule"
    assert response.tool_events[0].record_id is None


@pytest.mark.asyncio
async def test_write_request_without_tool_is_clarification_and_cannot_claim_success():
    provider = RecordingProvider(
        [make_response(text="好的，已記錄您今天下午散步二十分鐘。")]
    )
    service = AgentService(provider=provider, gateway=ToolGateway())

    response = await service.chat(
        ChatRequest(
            message="請幫我記錄：我今天下午散步二十分鐘。",
            session_id="s-clarify",
        )
    )

    assert response.operation_completed is False
    assert response.action_status.value == "clarification_required"
    assert "已記錄" not in response.reply
    assert "補充" in response.reply


@pytest.mark.asyncio
async def test_system_prompt_contains_server_taipei_date_and_timezone():
    provider = RecordingProvider([make_response(text="你好")])
    service = AgentService(provider=provider, gateway=ToolGateway())

    await service.chat(ChatRequest(message="你好", session_id="s-time"))

    prompt = provider.calls[0]["system_prompt"]
    assert "Asia/Taipei" in prompt
    assert datetime.now().year.__str__() in prompt


@pytest.mark.asyncio
async def test_successful_write_requires_record_id_and_returns_structured_tool_result():
    tool = ToolUseBlock(
        tool_use_id="write-tool",
        name="create_care_event",
        input={
            "event_type": "activity",
            "content": "散步二十分鐘",
            "event_time": future_time(),
            "idempotency_key": "write-idem",
        },
    )
    provider = RecordingProvider(
        [
            make_response(
                stop_reason="tool_use",
                tools=[tool],
                raw_content=[
                    {
                        "toolUse": {
                            "toolUseId": "write-tool",
                            "name": "create_care_event",
                            "input": tool.input,
                        }
                    }
                ],
            ),
            make_response(text="已記錄活動事件。"),
        ]
    )
    service = AgentService(provider=provider, gateway=ToolGateway())

    response = await service.chat(
        ChatRequest(
            message="請幫我記錄：我今天下午四點散步二十分鐘。",
            session_id="s-write",
        )
    )

    assert response.operation_completed is True
    assert response.action_status.value == "completed"
    assert response.tool_events[0].record_id

    second_messages = provider.calls[1]["messages"]
    result_block = second_messages[-1]["content"][0]["toolResult"]
    payload = result_block["content"][0]["json"]
    assert payload["success"] is True
    assert payload["status"] == "succeeded"
    assert payload["record_id"] == response.tool_events[0].record_id
