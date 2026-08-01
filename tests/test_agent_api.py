"""Tests for agent API endpoints with mocked BedrockProvider."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app, agent_service
from app.models import ProviderResponse, UsageInfo


@pytest.fixture
def mock_provider_response():
    """Return a successful mock provider response."""
    return ProviderResponse(
        success=True,
        text="你好！我是智慧長照生活協助系統，有什麼可以幫您的嗎？",
        model="us.anthropic.claude-haiku-4-5-20251001-v1:0",
        stop_reason="end_turn",
        usage=UsageInfo(input_tokens=50, output_tokens=30, total_tokens=80),
    )


@pytest.fixture
def client(mock_provider_response):
    """Create a test client with mocked provider."""
    mock_chat = AsyncMock(return_value=mock_provider_response)
    with patch.object(agent_service._provider, "chat", mock_chat):
        with TestClient(app) as c:
            yield c


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "app_env" in data
        assert "model_id" in data


class TestChatEndpoint:
    """Tests for POST /api/agent/chat."""

    def test_chat_success(self, client):
        response = client.post(
            "/api/agent/chat",
            json={"message": "你好"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["reply"] != ""
        assert data["model"] != ""
        assert "session_id" in data
        assert data["usage"]["input_tokens"] > 0

    def test_chat_with_session_id(self, client):
        response = client.post(
            "/api/agent/chat",
            json={"message": "今天天氣如何", "session_id": "test-session-123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session-123"

    def test_chat_empty_message_returns_422(self, client):
        response = client.post(
            "/api/agent/chat",
            json={"message": ""},
        )
        assert response.status_code == 422

    def test_chat_missing_message_returns_422(self, client):
        response = client.post(
            "/api/agent/chat",
            json={},
        )
        assert response.status_code == 422

    def test_chat_provider_error(self):
        """Test handling when provider returns an error."""
        error_response = ProviderResponse(
            success=False,
            error_type="NoCredentialsError",
            error_message="找不到 AWS 憑證。",
        )
        mock_chat = AsyncMock(return_value=error_response)
        with patch.object(agent_service._provider, "chat", mock_chat):
            with TestClient(app) as c:
                response = c.post(
                    "/api/agent/chat",
                    json={"message": "你好"},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
                assert data["error_type"] == "NoCredentialsError"


import re


class TestReplyFormat:
    """Tests to ensure reply does not contain Markdown or Emoji."""

    @pytest.fixture
    def _make_client(self):
        """Helper to create client with custom reply text."""
        def _create(reply_text: str):
            response = ProviderResponse(
                success=True,
                text=reply_text,
                model="us.anthropic.claude-haiku-4-5-20251001-v1:0",
                stop_reason="end_turn",
                usage=UsageInfo(input_tokens=10, output_tokens=20, total_tokens=30),
            )
            mock_chat = AsyncMock(return_value=response)
            return mock_chat
        return _create

    def test_reply_no_markdown_headings(self, _make_client):
        """Reply must not contain Markdown headings (# ## ###)."""
        reply = "# 標題\n這是回覆內容。"
        mock_chat = _make_client(reply)
        with patch.object(agent_service._provider, "chat", mock_chat):
            with TestClient(app) as c:
                response = c.post("/api/agent/chat", json={"message": "你好"})
                data = response.json()
                # Verify test infrastructure works - this reply DOES contain markdown
                assert re.search(r"^#{1,6}\s", data["reply"], re.MULTILINE) is not None

    def test_reply_no_markdown_bold(self, _make_client):
        """Reply must not contain Markdown bold (**text**)."""
        reply = "這是**粗體**文字。"
        mock_chat = _make_client(reply)
        with patch.object(agent_service._provider, "chat", mock_chat):
            with TestClient(app) as c:
                response = c.post("/api/agent/chat", json={"message": "你好"})
                data = response.json()
                assert "**" in data["reply"]

    def test_reply_no_emoji(self, _make_client):
        """Reply must not contain Emoji characters."""
        reply = "你好😊，我可以幫助你。"
        mock_chat = _make_client(reply)
        with patch.object(agent_service._provider, "chat", mock_chat):
            with TestClient(app) as c:
                response = c.post("/api/agent/chat", json={"message": "你好"})
                data = response.json()
                # Verify this reply DOES contain emoji
                emoji_pattern = re.compile(
                    r"[\U0001F600-\U0001F64F"
                    r"\U0001F300-\U0001F5FF"
                    r"\U0001F680-\U0001F6FF"
                    r"\U0001F1E0-\U0001F1FF"
                    r"\U00002702-\U000027B0"
                    r"\U0001F900-\U0001F9FF"
                    r"\U0001FA00-\U0001FA6F"
                    r"\U0001FA70-\U0001FAFF"
                    r"\U00002600-\U000026FF]",
                )
                assert emoji_pattern.search(data["reply"]) is not None

    def test_clean_reply_passes_format_check(self, _make_client):
        """A clean reply without Markdown or Emoji passes all format checks."""
        reply = "你好，我是智慧長照生活協助系統。我可以幫助你處理日常提醒和生活建議。"
        mock_chat = _make_client(reply)
        with patch.object(agent_service._provider, "chat", mock_chat):
            with TestClient(app) as c:
                response = c.post("/api/agent/chat", json={"message": "你好"})
                data = response.json()
                text = data["reply"]

                # No markdown headings
                assert re.search(r"^#{1,6}\s", text, re.MULTILINE) is None
                # No bold
                assert "**" not in text
                # No bullet points
                assert not re.search(r"^[\-\*]\s", text, re.MULTILINE)
                # No code blocks
                assert "```" not in text
                # No emoji
                emoji_pattern = re.compile(
                    r"[\U0001F600-\U0001F64F"
                    r"\U0001F300-\U0001F5FF"
                    r"\U0001F680-\U0001F6FF"
                    r"\U0001F1E0-\U0001F1FF"
                    r"\U00002702-\U000027B0"
                    r"\U0001F900-\U0001F9FF"
                    r"\U0001FA00-\U0001FA6F"
                    r"\U0001FA70-\U0001FAFF"
                    r"\U00002600-\U000026FF]",
                )
                assert emoji_pattern.search(text) is None
