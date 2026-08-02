from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.breeze_asr_service import BreezeASRService
from app.config import settings
from app.hybrid_asr_service import HybridASRService
from app.main import (
    agent_service,
    app,
    taiwanese_reply_translator,
    taiwanese_tts_service,
    whisper_service,
)
from app.models import ProviderResponse, UsageInfo
from app.taiwanese_speech import (
    SynthesizedSpeech,
    TaiwaneseReplyTranslator,
    TaiwaneseTranslation,
    _float_waveform_to_wav,
)
from app.whisper_service import WhisperTranscription, WhisperUnavailableError


class _FakeBreezePipeline:
    def __init__(self) -> None:
        self.calls: list[tuple[str, bool]] = []

    def __call__(self, path: str, *, return_timestamps: bool):
        self.calls.append((path, return_timestamps))
        assert Path(path).exists()
        return {
            "text": "我暗時九點欲食藥",
            "chunks": [{"timestamp": (0.0, 2.25), "text": "test"}],
        }


@pytest.mark.asyncio
async def test_breeze_service_loads_once_and_returns_taiwanese_trace() -> None:
    fake = _FakeBreezePipeline()
    service = BreezeASRService(
        enabled=True,
        pipeline_factory=lambda **_: fake,
    )

    first = await service.transcribe(
        audio_bytes=b"fake-audio",
        filename="voice.wav",
        language="nan-TW",
    )
    second = await service.transcribe(
        audio_bytes=b"fake-audio-2",
        filename="voice.wav",
        language="nan-TW",
    )

    assert first.text == "我暗時九點欲食藥"
    assert first.language == "nan-TW"
    assert first.provider == "breeze"
    assert first.duration_seconds == 2.25
    assert second.text == first.text
    assert len(fake.calls) == 2


class _ASRStub:
    def __init__(self, result: WhisperTranscription | Exception, enabled: bool = True):
        self.result = result
        self.enabled = enabled
        self.calls: list[str | None] = []

    async def transcribe(self, *, audio_bytes: bytes, filename: str, language: str | None = None):
        del audio_bytes, filename
        self.calls.append(language)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


@pytest.mark.asyncio
async def test_hybrid_router_uses_breeze_for_taiwanese_and_whisper_for_mandarin() -> None:
    zh = WhisperTranscription("你好", "zh", 0.9, 1.0, 1.0, 1, "small")
    nan = WhisperTranscription(
        "食飽未",
        "nan-TW",
        None,
        1.0,
        None,
        1,
        "breeze",
        provider="breeze",
    )
    whisper = _ASRStub(zh)
    breeze = _ASRStub(nan)
    router = HybridASRService(whisper=whisper, breeze=breeze)  # type: ignore[arg-type]

    nan_result = await router.transcribe(
        audio_bytes=b"x",
        filename="a.wav",
        language="nan-TW",
    )
    zh_result = await router.transcribe(
        audio_bytes=b"x",
        filename="a.wav",
        language="zh-TW",
    )

    assert nan_result.provider == "breeze"
    assert nan_result.requested_language == "nan-TW"
    assert zh_result.text == "你好"
    assert breeze.calls == ["nan-TW"]
    assert whisper.calls == ["zh"]


@pytest.mark.asyncio
async def test_hybrid_router_falls_back_when_primary_unavailable() -> None:
    zh = WhisperTranscription("fallback", "zh", 0.8, 1.0, 1.0, 1, "small")
    whisper = _ASRStub(zh)
    breeze = _ASRStub(WhisperUnavailableError("offline"))
    router = HybridASRService(whisper=whisper, breeze=breeze)  # type: ignore[arg-type]

    result = await router.transcribe(
        audio_bytes=b"x",
        filename="a.wav",
        language="nan-TW",
    )

    assert result.text == "fallback"
    assert breeze.calls == ["nan-TW"]
    assert whisper.calls == [None]


class _TranslationProvider:
    async def chat(self, messages, system_prompt, tool_config=None):
        del messages, system_prompt, tool_config
        return ProviderResponse(
            success=True,
            text='{"display_text":"好，我會佇 21:00 提醒你食藥。","tts_text":"Hó, guá ē tī 21:00 thê-sí lí chia̍h-io̍h."}',
            model="translation-test",
        )


@pytest.mark.asyncio
async def test_taiwanese_translation_preserves_agent_reply_literals() -> None:
    translator = TaiwaneseReplyTranslator(_TranslationProvider())  # type: ignore[arg-type]
    result = await translator.translate("好的，我會在 21:00 提醒你吃藥。")
    assert result.display_text == "好，我會佇 21:00 提醒你食藥。"
    assert "21:00" in result.tts_text


def test_wav_encoder_outputs_riff_wave() -> None:
    audio = _float_waveform_to_wav([0.0, 0.5, -0.5], 16000)
    assert audio.startswith(b"RIFF")
    assert b"WAVE" in audio[:16]


TAIWANESE_TRANSCRIPTION = WhisperTranscription(
    text="我暗時九點欲食藥",
    language="nan-TW",
    language_probability=None,
    duration_seconds=1.2,
    duration_after_vad_seconds=None,
    segment_count=1,
    model="MediaTek-Research/Breeze-ASR-26",
    provider="breeze",
    requested_language="nan-TW",
)


def test_voice_turn_translates_full_agent_reply_and_returns_taiwanese_audio() -> None:
    provider_response = ProviderResponse(
        success=True,
        text="好的，我會提醒你吃藥。",
        model="test-model",
        stop_reason="end_turn",
        usage=UsageInfo(input_tokens=5, output_tokens=3, total_tokens=8),
    )
    wav = _float_waveform_to_wav([0.0, 0.1, -0.1], 16000)

    with patch.object(
        whisper_service,
        "transcribe",
        AsyncMock(return_value=TAIWANESE_TRANSCRIPTION),
    ), patch.object(
        agent_service._provider,
        "chat",
        AsyncMock(return_value=provider_response),
    ), patch.object(
        taiwanese_reply_translator,
        "translate",
        AsyncMock(
            return_value=TaiwaneseTranslation(
                display_text="好，我會提醒你食藥。",
                tts_text="Hó, guá ē thê-sí lí chia̍h-io̍h.",
                model="translation-test",
            )
        ),
    ), patch.object(
        taiwanese_tts_service,
        "synthesize",
        AsyncMock(
            return_value=SynthesizedSpeech(
                audio_bytes=wav,
                content_type="audio/wav",
                sample_rate_hz=16000,
                model="tts-test",
            )
        ),
    ), patch.object(settings, "TAIWANESE_TTS_ENABLED", True):
        with TestClient(app) as client:
            response = client.post(
                "/api/voice/turn",
                files={"audio": ("voice.webm", b"fake", "audio/webm")},
                data={"session_id": "voice-nan-1", "language": "nan-TW"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["input_language"] == "nan-TW"
    assert data["reply_language"] == "nan-TW"
    assert data["agent"]["reply"] == "好的，我會提醒你吃藥。"
    assert data["translated_reply"] == "好，我會提醒你食藥。"
    assert base64.b64decode(data["speech_delivery"]["audio_base64"]) == wav
    assert data["speech_delivery"]["content_type"] == "audio/wav"
