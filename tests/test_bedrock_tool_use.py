"""Tests for Bedrock toolUse integration with mocked boto3."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import ChatRequest, ProviderResponse, ToolUseBlock, UsageInfo
from app.providers.bedrock import BedrockProvider
from app.services.agent_service import AgentService
from app.tools import ToolGateway


def make_event_time() -> str:
    """Create ISO timestamp with timezone."""
    return (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()


@pytest.fixture
def mock_bedrock_client():
    """Create a mocked boto3 bedrock-runtime client."""
    client = MagicMock()
    return client


@pytest.fixture
def provider_with_mock(mock_bedrock_client):
    """Create a BedrockProvider with mocked client."""
    with patch("boto3.Session") as mock_session:
        mock_session.return_value.client.return_value = mock_bedrock_client
        provider = BedrockProvider()
        provider._client = mock_bedrock_client
        yield provider


@pytest.fixture
def gateway():
    """Create a fresh gateway for testing."""
    return ToolGateway()


@pytest.fixture
def agent_service(provider_with_mock, gateway):
    """Create agent service with mocked provider and gateway."""
    return AgentService(provider=provider_with_mock, gateway=gateway)



class TestBedrockToolConfig:
    """Test that tool config is passed to Bedrock."""

    @pytest.mark.asyncio
    async def test_tool_config_passed_to_converse(
        self, provider_with_mock, mock_bedrock_client, gateway
    ):
        """Verify toolConfig is included in Converse API call."""
        # Setup mock response
        mock_bedrock_client.converse.return_value = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "好的，我可以幫你。"}],
                }
            },
            "stopReason": "end_turn",
            "usage": {"inputTokens": 10, "outputTokens": 5},
        }

        # Get tool config from gateway
        from app.tools import DemoAuthContextFactory
        auth = DemoAuthContextFactory.create_resident(
            requester_id="test", persona_id="p1",
            session_id="s1", request_id="r1"
        )
        tool_config = gateway.get_bedrock_tool_config(auth)

        # Call provider
        result = await provider_with_mock.chat(
            messages=[{"role": "user", "content": "你好"}],
            system_prompt="test",
            tool_config=tool_config,
        )

        # Verify converse was called with toolConfig
        call_args = mock_bedrock_client.converse.call_args
        assert "toolConfig" in call_args.kwargs or (
            len(call_args.args) > 0 and "toolConfig" in str(call_args)
        )


class TestToolUseResponse:
    """Test parsing toolUse responses from Bedrock."""

    @pytest.mark.asyncio
    async def test_parse_tool_use_blocks(self, provider_with_mock, mock_bedrock_client):
        """Parse toolUse blocks from Converse response."""
        mock_bedrock_client.converse.return_value = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {"text": "讓我幫你記錄這個事件。"},
                        {
                            "toolUse": {
                                "toolUseId": "tool-123",
                                "name": "create_care_event",
                                "input": {
                                    "event_type": "activity",
                                    "content": "散步",
                                    "event_time": make_event_time(),
                                    "idempotency_key": "idem-123",
                                },
                            }
                        },
                    ],
                }
            },
            "stopReason": "tool_use",
            "usage": {"inputTokens": 20, "outputTokens": 15},
        }

        result = await provider_with_mock.chat(
            messages=[{"role": "user", "content": "我剛散步30分鐘"}],
            system_prompt="test",
        )

        assert result.success is True
        assert result.stop_reason == "tool_use"
        assert len(result.tool_use_blocks) == 1
        assert result.tool_use_blocks[0].tool_use_id == "tool-123"
        assert result.tool_use_blocks[0].name == "create_care_event"
        assert result.tool_use_blocks[0].input["event_type"] == "activity"

    @pytest.mark.asyncio
    async def test_raw_content_preserved(self, provider_with_mock, mock_bedrock_client):
        """Raw content blocks are preserved for message history."""
        content_blocks = [
            {"text": "思考中..."},
            {
                "toolUse": {
                    "toolUseId": "tool-456",
                    "name": "get_user_schedule",
                    "input": {},
                }
            },
        ]
        mock_bedrock_client.converse.return_value = {
            "output": {"message": {"role": "assistant", "content": content_blocks}},
            "stopReason": "tool_use",
            "usage": {"inputTokens": 10, "outputTokens": 10},
        }

        result = await provider_with_mock.chat(
            messages=[{"role": "user", "content": "今天有什麼行程"}],
            system_prompt="test",
        )

        assert result.raw_content == content_blocks



class TestAgentServiceToolLoop:
    """Test AgentService tool loop behavior."""

    @pytest.mark.asyncio
    async def test_simple_chat_no_tools(self, agent_service, mock_bedrock_client):
        """Simple chat without tools returns directly."""
        mock_bedrock_client.converse.return_value = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "你好！有什麼可以幫你的嗎？"}],
                }
            },
            "stopReason": "end_turn",
            "usage": {"inputTokens": 10, "outputTokens": 10},
        }

        request = ChatRequest(message="你好")
        response = await agent_service.chat(request)

        assert response.success is True
        assert "你好" in response.reply
        assert response.requires_confirmation is False

    @pytest.mark.asyncio
    async def test_tool_execution_success(self, agent_service, mock_bedrock_client):
        """Tool is executed and result returned to model."""
        event_time = make_event_time()

        # First call: model wants to use tool
        # Second call: model responds after seeing tool result
        mock_bedrock_client.converse.side_effect = [
            {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "toolUse": {
                                    "toolUseId": "tool-001",
                                    "name": "create_care_event",
                                    "input": {
                                        "event_type": "activity",
                                        "content": "散步30分鐘",
                                        "event_time": event_time,
                                        "idempotency_key": "idem-001",
                                    },
                                }
                            }
                        ],
                    }
                },
                "stopReason": "tool_use",
                "usage": {"inputTokens": 20, "outputTokens": 30},
            },
            {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"text": "好的，我已經幫你記錄了散步30分鐘的活動。"}],
                    }
                },
                "stopReason": "end_turn",
                "usage": {"inputTokens": 50, "outputTokens": 20},
            },
        ]

        request = ChatRequest(message="我剛散步30分鐘", session_id="test-session")
        response = await agent_service.chat(request)

        assert response.success is True
        assert "已經" in response.reply or "記錄" in response.reply
        assert response.session_id == "test-session"
        # Verify tool was executed
        events = agent_service.gateway.repository.get_all_events()
        assert len(events) == 1
        assert events[0].content == "散步30分鐘"

    @pytest.mark.asyncio
    async def test_medication_requires_confirmation(
        self, agent_service, mock_bedrock_client
    ):
        """Medication event requires confirmation before execution."""
        event_time = make_event_time()

        mock_bedrock_client.converse.return_value = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": "tool-med",
                                "name": "create_care_event",
                                "input": {
                                    "event_type": "medication",
                                    "content": "服用降血壓藥",
                                    "event_time": event_time,
                                    "idempotency_key": "idem-med",
                                },
                            }
                        }
                    ],
                }
            },
            "stopReason": "tool_use",
            "usage": {"inputTokens": 20, "outputTokens": 30},
        }

        request = ChatRequest(message="我剛吃了降血壓藥")
        response = await agent_service.chat(request)

        # Should return awaiting confirmation
        assert response.success is True
        assert response.requires_confirmation is True
        assert response.confirmation_token is not None
        assert "用藥" in response.confirmation_summary

        # Event should NOT be created yet
        events = agent_service.gateway.repository.get_all_events()
        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_confirmation_flow_completes(
        self, agent_service, mock_bedrock_client
    ):
        """After confirmation, tool executes successfully."""
        event_time = make_event_time()

        mock_bedrock_client.converse.return_value = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": "tool-med-2",
                                "name": "create_care_event",
                                "input": {
                                    "event_type": "medication",
                                    "content": "服用維他命",
                                    "event_time": event_time,
                                    "idempotency_key": "idem-med-2",
                                },
                            }
                        }
                    ],
                }
            },
            "stopReason": "tool_use",
            "usage": {"inputTokens": 20, "outputTokens": 30},
        }

        # Step 1: Initial request returns confirmation needed
        request1 = ChatRequest(message="我吃了維他命")
        response1 = await agent_service.chat(request1)
        assert response1.requires_confirmation is True
        token = response1.confirmation_token

        # Step 2: Confirm the operation
        request2 = ChatRequest(
            message="確認",
            session_id=response1.session_id,
            confirmation_token=token,
        )
        response2 = await agent_service.chat(request2)

        assert response2.success is True
        # Event should now be created
        events = agent_service.gateway.repository.get_all_events()
        assert len(events) == 1
        assert events[0].content == "服用維他命"



class TestToolLoopLimits:
    """Test tool loop safety limits."""

    @pytest.mark.asyncio
    async def test_max_tools_per_turn(self, agent_service, mock_bedrock_client):
        """Only 2 tools can execute per turn."""
        event_time = make_event_time()

        # Model wants to call 3 tools
        mock_bedrock_client.converse.side_effect = [
            {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "toolUse": {
                                    "toolUseId": "tool-1",
                                    "name": "create_care_event",
                                    "input": {
                                        "event_type": "activity",
                                        "content": "活動1",
                                        "event_time": event_time,
                                        "idempotency_key": "idem-1",
                                    },
                                }
                            },
                            {
                                "toolUse": {
                                    "toolUseId": "tool-2",
                                    "name": "create_care_event",
                                    "input": {
                                        "event_type": "activity",
                                        "content": "活動2",
                                        "event_time": event_time,
                                        "idempotency_key": "idem-2",
                                    },
                                }
                            },
                            {
                                "toolUse": {
                                    "toolUseId": "tool-3",
                                    "name": "create_care_event",
                                    "input": {
                                        "event_type": "activity",
                                        "content": "活動3",
                                        "event_time": event_time,
                                        "idempotency_key": "idem-3",
                                    },
                                }
                            },
                        ],
                    }
                },
                "stopReason": "tool_use",
                "usage": {"inputTokens": 30, "outputTokens": 50},
            },
            {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"text": "已記錄兩個活動。"}],
                    }
                },
                "stopReason": "end_turn",
                "usage": {"inputTokens": 60, "outputTokens": 10},
            },
        ]

        request = ChatRequest(message="記錄三個活動")
        response = await agent_service.chat(request)

        # Only 2 events should be created
        events = agent_service.gateway.repository.get_all_events()
        assert len(events) == 2

    @pytest.mark.asyncio
    async def test_max_converse_rounds(self, agent_service, mock_bedrock_client):
        """Max 3 Converse round trips."""
        event_time = make_event_time()

        # Model keeps requesting tools (simulating infinite loop)
        tool_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": "tool-loop",
                                "name": "get_user_schedule",
                                "input": {},
                            }
                        }
                    ],
                }
            },
            "stopReason": "tool_use",
            "usage": {"inputTokens": 10, "outputTokens": 10},
        }

        # Return tool_use 10 times (exceeds max of 3)
        mock_bedrock_client.converse.side_effect = [tool_response] * 10

        request = ChatRequest(message="查詢行程")
        response = await agent_service.chat(request)

        # Should stop after max rounds
        assert response.success is True
        assert "複雜" in response.reply or "稍後" in response.reply
        # converse should be called max 3 times
        assert mock_bedrock_client.converse.call_count <= 3


class TestToolResultFormat:
    """Test tool result is formatted correctly for Bedrock."""

    @pytest.mark.asyncio
    async def test_tool_result_preserves_tool_use_id(
        self, agent_service, mock_bedrock_client
    ):
        """toolResult uses same toolUseId as toolUse."""
        event_time = make_event_time()

        mock_bedrock_client.converse.side_effect = [
            {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "toolUse": {
                                    "toolUseId": "unique-id-12345",
                                    "name": "create_care_event",
                                    "input": {
                                        "event_type": "meal",
                                        "content": "午餐",
                                        "event_time": event_time,
                                        "idempotency_key": "idem-meal",
                                    },
                                }
                            }
                        ],
                    }
                },
                "stopReason": "tool_use",
                "usage": {"inputTokens": 20, "outputTokens": 20},
            },
            {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"text": "已記錄午餐。"}],
                    }
                },
                "stopReason": "end_turn",
                "usage": {"inputTokens": 40, "outputTokens": 10},
            },
        ]

        request = ChatRequest(message="記錄午餐")
        await agent_service.chat(request)

        # Check second call has toolResult with matching ID
        second_call = mock_bedrock_client.converse.call_args_list[1]
        messages = second_call.kwargs.get("messages", [])

        # Find user message with toolResult
        tool_result_msg = None
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", [])
                for block in content:
                    if "toolResult" in block:
                        tool_result_msg = block
                        break

        assert tool_result_msg is not None
        assert tool_result_msg["toolResult"]["toolUseId"] == "unique-id-12345"


class TestNoSuccessClaimBeforeSuccess:
    """Test that success is only claimed after tool succeeds."""

    @pytest.mark.asyncio
    async def test_failed_tool_shows_failure(
        self, agent_service, mock_bedrock_client
    ):
        """Failed tool execution reports error to model."""
        # Model tries to use unknown tool
        mock_bedrock_client.converse.side_effect = [
            {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "toolUse": {
                                    "toolUseId": "tool-unknown",
                                    "name": "delete_all_data",  # Unknown tool
                                    "input": {},
                                }
                            }
                        ],
                    }
                },
                "stopReason": "tool_use",
                "usage": {"inputTokens": 20, "outputTokens": 20},
            },
            {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"text": "抱歉，我無法執行這個操作。"}],
                    }
                },
                "stopReason": "end_turn",
                "usage": {"inputTokens": 40, "outputTokens": 10},
            },
        ]

        request = ChatRequest(message="刪除所有資料")
        response = await agent_service.chat(request)

        # Check that error was passed to model
        second_call = mock_bedrock_client.converse.call_args_list[1]
        messages = second_call.kwargs.get("messages", [])

        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", [])
                for block in content:
                    if "toolResult" in block:
                        assert block["toolResult"]["status"] == "error"



class TestToolEventsAndActionStatus:
    """Test tool_events and action_status in response."""

    @pytest.mark.asyncio
    async def test_no_action_for_simple_chat(self, agent_service, mock_bedrock_client):
        """Simple chat has no_action status."""
        mock_bedrock_client.converse.return_value = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "你好！"}],
                }
            },
            "stopReason": "end_turn",
            "usage": {"inputTokens": 10, "outputTokens": 5},
        }

        request = ChatRequest(message="你好")
        response = await agent_service.chat(request)

        assert response.action_status.value == "no_action"
        assert response.operation_completed is False
        assert response.tool_events == []

    @pytest.mark.asyncio
    async def test_completed_status_with_successful_tool(
        self, agent_service, mock_bedrock_client
    ):
        """Successful tool sets completed status and operation_completed=True."""
        event_time = make_event_time()

        mock_bedrock_client.converse.side_effect = [
            {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "toolUse": {
                                    "toolUseId": "tool-success",
                                    "name": "create_care_event",
                                    "input": {
                                        "event_type": "activity",
                                        "content": "散步",
                                        "event_time": event_time,
                                        "idempotency_key": "idem-success",
                                    },
                                }
                            }
                        ],
                    }
                },
                "stopReason": "tool_use",
                "usage": {"inputTokens": 20, "outputTokens": 20},
            },
            {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"text": "已記錄。"}],
                    }
                },
                "stopReason": "end_turn",
                "usage": {"inputTokens": 40, "outputTokens": 10},
            },
        ]

        request = ChatRequest(message="記錄散步")
        response = await agent_service.chat(request)

        assert response.action_status.value == "completed"
        assert response.operation_completed is True
        assert len(response.tool_events) == 1
        event = response.tool_events[0]
        assert event.tool_name == "create_care_event"
        assert event.status == "succeeded"
        assert event.success is True
        assert event.record_id is not None
        # Verify no sensitive data
        assert event.error_code is None

    @pytest.mark.asyncio
    async def test_confirmation_required_status(
        self, agent_service, mock_bedrock_client
    ):
        """Medication triggers confirmation_required status."""
        event_time = make_event_time()

        mock_bedrock_client.converse.return_value = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": "tool-med-conf",
                                "name": "create_care_event",
                                "input": {
                                    "event_type": "medication",
                                    "content": "降血壓藥",
                                    "event_time": event_time,
                                    "idempotency_key": "idem-med-conf",
                                },
                            }
                        }
                    ],
                }
            },
            "stopReason": "tool_use",
            "usage": {"inputTokens": 20, "outputTokens": 20},
        }

        request = ChatRequest(message="吃藥")
        response = await agent_service.chat(request)

        assert response.action_status.value == "confirmation_required"
        assert response.operation_completed is False
        assert response.requires_confirmation is True
        assert len(response.tool_events) == 1
        event = response.tool_events[0]
        assert event.status == "awaiting_confirmation"
        assert event.success is False

    @pytest.mark.asyncio
    async def test_denied_status_for_unknown_tool(
        self, agent_service, mock_bedrock_client
    ):
        """Unknown tool sets denied status."""
        mock_bedrock_client.converse.side_effect = [
            {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "toolUse": {
                                    "toolUseId": "tool-bad",
                                    "name": "execute_sql",
                                    "input": {},
                                }
                            }
                        ],
                    }
                },
                "stopReason": "tool_use",
                "usage": {"inputTokens": 20, "outputTokens": 20},
            },
            {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"text": "無法執行。"}],
                    }
                },
                "stopReason": "end_turn",
                "usage": {"inputTokens": 40, "outputTokens": 10},
            },
        ]

        request = ChatRequest(message="執行SQL")
        response = await agent_service.chat(request)

        # No successful tool, so failed
        assert response.action_status.value == "denied"
        assert response.operation_completed is False
        assert len(response.tool_events) == 1
        event = response.tool_events[0]
        assert event.status == "denied"
        assert event.success is False
        assert event.error_code == "UNKNOWN_TOOL"

    @pytest.mark.asyncio
    async def test_tool_event_no_sensitive_data(
        self, agent_service, mock_bedrock_client
    ):
        """ToolEvent does not contain sensitive data."""
        event_time = make_event_time()

        mock_bedrock_client.converse.side_effect = [
            {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "toolUse": {
                                    "toolUseId": "tool-sensitive",
                                    "name": "create_care_event",
                                    "input": {
                                        "event_type": "meal",
                                        "content": "敏感的用餐資料",
                                        "event_time": event_time,
                                        "idempotency_key": "idem-sensitive",
                                    },
                                }
                            }
                        ],
                    }
                },
                "stopReason": "tool_use",
                "usage": {"inputTokens": 20, "outputTokens": 20},
            },
            {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"text": "已記錄。"}],
                    }
                },
                "stopReason": "end_turn",
                "usage": {"inputTokens": 40, "outputTokens": 10},
            },
        ]

        request = ChatRequest(message="記錄用餐")
        response = await agent_service.chat(request)

        # Verify tool_events structure
        for event in response.tool_events:
            # Check only allowed fields exist
            event_dict = event.model_dump()
            allowed_keys = {
                "tool_call_id", "tool_name", "status", "success",
                "record_id", "error_code", "idempotency_replayed"
            }
            assert set(event_dict.keys()) == allowed_keys
            # Verify no content leaked
            assert "敏感" not in str(event_dict)
            assert "content" not in event_dict

    @pytest.mark.asyncio
    async def test_confirmation_complete_sets_operation_completed(
        self, agent_service, mock_bedrock_client
    ):
        """Confirmed tool sets operation_completed=True."""
        event_time = make_event_time()

        mock_bedrock_client.converse.return_value = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": "tool-conf-done",
                                "name": "create_care_event",
                                "input": {
                                    "event_type": "medication",
                                    "content": "維他命",
                                    "event_time": event_time,
                                    "idempotency_key": "idem-conf-done",
                                },
                            }
                        }
                    ],
                }
            },
            "stopReason": "tool_use",
            "usage": {"inputTokens": 20, "outputTokens": 20},
        }

        # Step 1: Get confirmation token
        request1 = ChatRequest(message="吃維他命")
        response1 = await agent_service.chat(request1)
        assert response1.action_status.value == "confirmation_required"
        token = response1.confirmation_token

        # Step 2: Confirm
        request2 = ChatRequest(
            message="確認",
            session_id=response1.session_id,
            confirmation_token=token,
        )
        response2 = await agent_service.chat(request2)

        assert response2.success is True
        assert response2.action_status.value == "completed"
        assert response2.operation_completed is True
        assert len(response2.tool_events) == 1
        assert response2.tool_events[0].status == "succeeded"
        assert response2.tool_events[0].success is True
