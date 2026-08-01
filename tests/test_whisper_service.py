from types import SimpleNamespace

import pytest

from app.whisper_service import EmptyTranscriptionError, WhisperService


class _FakeModel:
    def __init__(self, text: str = "請提醒我喝水") -> None:
        self.text = text
        self.calls: list[tuple[str, dict]] = []

    def transcribe(self, path: str, **kwargs):
        self.calls.append((path, kwargs))
        info = SimpleNamespace(
            language="zh",
            language_probability=0.99,
            duration=2.5,
            duration_after_vad=1.8,
        )
        return [SimpleNamespace(text=self.text)], info


@pytest.mark.asyncio
async def test_whisper_service_transcribes_and_returns_trace() -> None:
    model = _FakeModel()
    service = WhisperService(
        model_size="small",
        model_factory=lambda **_: model,
    )

    result = await service.transcribe(
        audio_bytes=b"fake-audio",
        filename="sample.wav",
        language="zh",
    )

    assert result.text == "請提醒我喝水"
    assert result.language == "zh"
    assert result.language_probability == 0.99
    assert result.segment_count == 1
    assert result.model == "small"
    assert model.calls[0][1]["language"] == "zh"


@pytest.mark.asyncio
async def test_whisper_service_rejects_empty_transcript() -> None:
    service = WhisperService(
        model_factory=lambda **_: _FakeModel(text="   "),
    )

    with pytest.raises(EmptyTranscriptionError):
        await service.transcribe(
            audio_bytes=b"fake-audio",
            filename="sample.wav",
        )
