from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import agent_service, app, local_speech_player, whisper_service
from app.models import ProviderResponse, UsageInfo
from app.output import DeliveryResult
from app.whisper_service import WhisperTranscription


TRANSCRIPTION = WhisperTranscription(
    text="你好",
    language="zh",
    language_probability=0.98,
    duration_seconds=1.2,
    duration_after_vad_seconds=0.9,
    segment_count=1,
    model="small",
)


def test_voice_transcribe_endpoint() -> None:
    with patch.object(
        whisper_service,
        "transcribe",
        AsyncMock(return_value=TRANSCRIPTION),
    ):
        with TestClient(app) as client:
            response = client.post(
                "/api/voice/transcribe",
                files={"audio": ("voice.wav", b"fake", "audio/wav")},
                data={"language": "zh"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["transcript"] == "你好"
    assert data["trace"]["language"] == "zh"
    assert data["trace"]["segment_count"] == 1


def test_voice_turn_runs_normal_agent_pipeline() -> None:
    provider_response = ProviderResponse(
        success=True,
        text="您好。",
        model="test-model",
        stop_reason="end_turn",
        usage=UsageInfo(input_tokens=5, output_tokens=3, total_tokens=8),
    )
    with patch.object(
        whisper_service,
        "transcribe",
        AsyncMock(return_value=TRANSCRIPTION),
    ), patch.object(
        agent_service._provider,
        "chat",
        AsyncMock(return_value=provider_response),
    ), patch.object(
        local_speech_player,
        "speak",
        return_value=DeliveryResult(ok=True, backend="test_tts"),
    ) as speak:
        with TestClient(app) as client:
            response = client.post(
                "/api/voice/turn",
                files={"audio": ("voice.webm", b"fake", "audio/webm")},
                data={"session_id": "voice-session-1"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["transcript"] == "你好"
    assert data["agent"]["session_id"] == "voice-session-1"
    assert data["agent"]["reply"] == "您好。"
    assert data["agent"]["input_guard"]["allowed"] is True
    assert data["speech_delivery"]["ok"] is True
    assert data["speech_delivery"]["backend"] == "test_tts"
    speak.assert_called_once_with("您好。")


def test_voice_endpoint_rejects_unsupported_media_type() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/voice/transcribe",
            files={"audio": ("note.txt", b"not-audio", "text/plain")},
        )
    assert response.status_code == 415
