"""Lazy local faster-whisper transcription service.

Audio bytes are written to a temporary file only for the duration of one
transcription and are always deleted. Model loading and inference are
serialized to avoid duplicate model loads and excessive memory use.
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


class WhisperUnavailableError(RuntimeError):
    """Raised when faster-whisper is not installed or cannot load."""


class EmptyTranscriptionError(ValueError):
    """Raised when Whisper produces no meaningful text."""


@dataclass(frozen=True)
class WhisperTranscription:
    text: str
    language: str | None
    language_probability: float | None
    duration_seconds: float | None
    duration_after_vad_seconds: float | None
    segment_count: int
    model: str


ModelFactory = Callable[..., Any]


def _default_model_factory(**kwargs: Any) -> Any:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:  # pragma: no cover - depends on optional package
        raise WhisperUnavailableError(
            "faster-whisper 尚未安裝，請執行：uv sync --extra voice"
        ) from exc
    return WhisperModel(**kwargs)


class WhisperService:
    """Thread-safe lazy wrapper around faster-whisper."""

    def __init__(
        self,
        *,
        enabled: bool = True,
        model_size: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
        download_root: str | None = None,
        beam_size: int = 5,
        vad_filter: bool = True,
        model_factory: ModelFactory | None = None,
    ) -> None:
        self.enabled = enabled
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.download_root = download_root
        self.beam_size = beam_size
        self.vad_filter = vad_filter
        self._model_factory = model_factory or _default_model_factory
        self._model: Any | None = None
        self._lock = threading.Lock()

    @property
    def loaded(self) -> bool:
        return self._model is not None

    async def load_model(self) -> None:
        if not self.enabled:
            raise WhisperUnavailableError("Whisper transcription is disabled")
        await asyncio.to_thread(self._ensure_model)

    async def transcribe(
        self,
        *,
        audio_bytes: bytes,
        filename: str,
        language: str | None = None,
    ) -> WhisperTranscription:
        if not self.enabled:
            raise WhisperUnavailableError("Whisper transcription is disabled")
        if not audio_bytes:
            raise EmptyTranscriptionError("音訊內容為空")
        return await asyncio.to_thread(
            self._transcribe_sync,
            audio_bytes,
            filename,
            language,
        )

    def _ensure_model(self) -> Any:
        with self._lock:
            if self._model is not None:
                return self._model
            kwargs: dict[str, Any] = {
                "model_size_or_path": self.model_size,
                "device": self.device,
                "compute_type": self.compute_type,
            }
            if self.download_root:
                kwargs["download_root"] = self.download_root
            logger.info(
                "Loading faster-whisper model=%s device=%s compute_type=%s",
                self.model_size,
                self.device,
                self.compute_type,
            )
            try:
                self._model = self._model_factory(**kwargs)
            except TypeError:
                # Test doubles and older wrappers may use the model name as a
                # positional argument.
                model_name = kwargs.pop("model_size_or_path")
                self._model = self._model_factory(model_name, **kwargs)
            except WhisperUnavailableError:
                raise
            except Exception as exc:
                raise WhisperUnavailableError(f"Whisper 模型載入失敗：{exc}") from exc
            return self._model

    def _transcribe_sync(
        self,
        audio_bytes: bytes,
        filename: str,
        language: str | None,
    ) -> WhisperTranscription:
        suffix = Path(filename).suffix.lower() or ".webm"
        temp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
                temp.write(audio_bytes)
                temp.flush()
                temp_path = temp.name

            # Model load and inference are intentionally serialized because a
            # local CPU model may consume substantial memory.
            with self._lock:
                if self._model is None:
                    kwargs: dict[str, Any] = {
                        "model_size_or_path": self.model_size,
                        "device": self.device,
                        "compute_type": self.compute_type,
                    }
                    if self.download_root:
                        kwargs["download_root"] = self.download_root
                    try:
                        self._model = self._model_factory(**kwargs)
                    except TypeError:
                        model_name = kwargs.pop("model_size_or_path")
                        self._model = self._model_factory(model_name, **kwargs)
                    except Exception as exc:
                        raise WhisperUnavailableError(
                            f"Whisper 模型載入失敗：{exc}"
                        ) from exc

                segments, info = self._model.transcribe(
                    temp_path,
                    language=language,
                    beam_size=self.beam_size,
                    vad_filter=self.vad_filter,
                )
                segment_list = list(segments)

            text = "".join(str(segment.text) for segment in segment_list).strip()
            if not text:
                raise EmptyTranscriptionError("沒有辨識到有效語音")

            return WhisperTranscription(
                text=text,
                language=getattr(info, "language", None),
                language_probability=_optional_float(
                    getattr(info, "language_probability", None)
                ),
                duration_seconds=_optional_float(getattr(info, "duration", None)),
                duration_after_vad_seconds=_optional_float(
                    getattr(info, "duration_after_vad", None)
                ),
                segment_count=len(segment_list),
                model=self.model_size,
            )
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except FileNotFoundError:
                    pass


def _optional_float(value: Any) -> float | None:
    return float(value) if value is not None else None
