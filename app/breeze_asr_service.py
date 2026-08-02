"""Lazy Breeze-ASR-26 service for Taiwanese (Min Nan) speech.

The model is loaded once per process and inference is serialized to avoid
concurrent model initialization and excessive memory use. Audio is written to
a temporary file only for the duration of one transcription.
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, Callable

from app.whisper_service import (
    EmptyTranscriptionError,
    WhisperTranscription,
    WhisperUnavailableError,
)

logger = logging.getLogger(__name__)

PipelineFactory = Callable[..., Any]


def _default_pipeline_factory(**kwargs: Any) -> Any:
    try:
        import torch
        from transformers import pipeline
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise WhisperUnavailableError(
            "Breeze ASR 依賴尚未安裝，請執行：uv sync --extra bilingual-voice"
        ) from exc

    requested_device = kwargs.pop("requested_device", "auto")
    if requested_device == "auto":
        if torch.backends.mps.is_available():
            device: str | int = "mps"
        elif torch.cuda.is_available():
            device = 0
        else:
            device = -1
    elif requested_device == "cuda":
        device = 0
    elif requested_device == "cpu":
        device = -1
    else:
        device = requested_device

    return pipeline(
        task="automatic-speech-recognition",
        device=device,
        **kwargs,
    )


class BreezeASRService:
    """Thread-safe lazy wrapper around MediaTek Breeze-ASR-26."""

    def __init__(
        self,
        *,
        enabled: bool = False,
        model_id: str = "MediaTek-Research/Breeze-ASR-26",
        device: str = "auto",
        pipeline_factory: PipelineFactory | None = None,
    ) -> None:
        self.enabled = enabled
        self.model_id = model_id
        self.device = device
        self._pipeline_factory = pipeline_factory or _default_pipeline_factory
        self._pipeline: Any | None = None
        self._lock = threading.Lock()

    @property
    def loaded(self) -> bool:
        return self._pipeline is not None

    async def load_model(self) -> None:
        if not self.enabled:
            raise WhisperUnavailableError("Breeze ASR is disabled")
        await asyncio.to_thread(self._ensure_pipeline)

    async def transcribe(
        self,
        *,
        audio_bytes: bytes,
        filename: str,
        language: str | None = None,
    ) -> WhisperTranscription:
        del language  # Breeze model is selected explicitly for Taiwanese input.
        if not self.enabled:
            raise WhisperUnavailableError("Breeze ASR is disabled")
        if not audio_bytes:
            raise EmptyTranscriptionError("音訊內容為空")
        return await asyncio.to_thread(self._transcribe_sync, audio_bytes, filename)

    def _ensure_pipeline(self) -> Any:
        with self._lock:
            if self._pipeline is not None:
                return self._pipeline
            logger.info(
                "Loading Breeze ASR model=%s device=%s",
                self.model_id,
                self.device,
            )
            try:
                self._pipeline = self._pipeline_factory(
                    model=self.model_id,
                    requested_device=self.device,
                )
            except WhisperUnavailableError:
                raise
            except Exception as exc:
                raise WhisperUnavailableError(
                    f"Breeze ASR 模型載入失敗：{exc}"
                ) from exc
            return self._pipeline

    def _transcribe_sync(
        self,
        audio_bytes: bytes,
        filename: str,
    ) -> WhisperTranscription:
        suffix = Path(filename).suffix.lower() or ".webm"
        temp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
                temp.write(audio_bytes)
                temp.flush()
                temp_path = temp.name

            with self._lock:
                pipeline_instance = self._pipeline
                if pipeline_instance is None:
                    pipeline_instance = self._pipeline_factory(
                        model=self.model_id,
                        requested_device=self.device,
                    )
                    self._pipeline = pipeline_instance
                result = pipeline_instance(temp_path, return_timestamps=True)

            text = str(result.get("text", "")).strip()
            if not text:
                raise EmptyTranscriptionError("沒有辨識到有效台語語音")

            chunks = result.get("chunks") or []
            duration = _duration_from_chunks(chunks)
            return WhisperTranscription(
                text=text,
                language="nan-TW",
                language_probability=None,
                duration_seconds=duration,
                duration_after_vad_seconds=None,
                segment_count=max(1, len(chunks)),
                model=self.model_id,
                provider="breeze",
                requested_language="nan-TW",
            )
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except FileNotFoundError:
                    pass


def _duration_from_chunks(chunks: list[dict[str, Any]]) -> float | None:
    latest: float | None = None
    for chunk in chunks:
        timestamp = chunk.get("timestamp")
        if not isinstance(timestamp, (list, tuple)) or len(timestamp) != 2:
            continue
        end = timestamp[1]
        if isinstance(end, (int, float)):
            latest = max(latest or 0.0, float(end))
    return latest
