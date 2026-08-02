"""Language-aware ASR router for Mandarin and Taiwanese speech."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from app.breeze_asr_service import BreezeASRService
from app.whisper_service import (
    EmptyTranscriptionError,
    WhisperService,
    WhisperTranscription,
    WhisperUnavailableError,
)

logger = logging.getLogger(__name__)

TAIWANESE_LANGUAGE_ALIASES = {
    "nan",
    "nan-tw",
    "taiwanese",
    "taigi",
    "hokkien",
    "台語",
    "臺語",
}
MANDARIN_LANGUAGE_ALIASES = {
    "zh",
    "zh-tw",
    "zh-hant",
    "mandarin",
    "中文",
    "國語",
}


def normalize_voice_language(language: str | None) -> str:
    normalized = (language or "auto").strip().lower()
    if normalized in TAIWANESE_LANGUAGE_ALIASES:
        return "nan-TW"
    if normalized in MANDARIN_LANGUAGE_ALIASES:
        return "zh-TW"
    return "auto"


def is_taiwanese_language(language: str | None) -> bool:
    return normalize_voice_language(language) == "nan-TW"


class HybridASRService:
    """Route explicit Mandarin input to Whisper and Taiwanese input to Breeze.

    Automatic mode uses the configured primary provider. Fallback occurs only
    when the selected provider is unavailable or returns an empty transcript;
    it does not run both large models for every request.
    """

    def __init__(
        self,
        *,
        whisper: WhisperService,
        breeze: BreezeASRService,
        mode: str = "hybrid",
        auto_primary: str = "whisper",
        fallback_enabled: bool = True,
    ) -> None:
        self.whisper = whisper
        self.breeze = breeze
        self.mode = mode.strip().lower()
        self.auto_primary = auto_primary.strip().lower()
        self.fallback_enabled = fallback_enabled

    async def transcribe(
        self,
        *,
        audio_bytes: bytes,
        filename: str,
        language: str | None = None,
    ) -> WhisperTranscription:
        requested = normalize_voice_language(language)
        primary_name = self._select_primary(requested)
        secondary_name = "breeze" if primary_name == "whisper" else "whisper"

        try:
            result = await self._call(
                primary_name,
                audio_bytes=audio_bytes,
                filename=filename,
                requested_language=requested,
            )
            return _with_requested_language(result, requested)
        except (WhisperUnavailableError, EmptyTranscriptionError) as primary_error:
            if not self.fallback_enabled or not self._provider_enabled(secondary_name):
                raise
            logger.warning(
                "ASR primary failed; trying fallback primary=%s fallback=%s error=%s",
                primary_name,
                secondary_name,
                type(primary_error).__name__,
            )
            result = await self._call(
                secondary_name,
                audio_bytes=audio_bytes,
                filename=filename,
                requested_language=requested,
            )
            return _with_requested_language(result, requested)

    def _select_primary(self, requested: str) -> str:
        if self.mode == "whisper":
            return "whisper"
        if self.mode == "breeze":
            return "breeze"
        if requested == "nan-TW":
            return "breeze"
        if requested == "zh-TW":
            return "whisper"
        return "breeze" if self.auto_primary == "breeze" else "whisper"

    def _provider_enabled(self, name: str) -> bool:
        if name == "breeze":
            return self.breeze.enabled
        return self.whisper.enabled

    async def _call(
        self,
        provider: str,
        *,
        audio_bytes: bytes,
        filename: str,
        requested_language: str,
    ) -> WhisperTranscription:
        if provider == "breeze":
            return await self.breeze.transcribe(
                audio_bytes=audio_bytes,
                filename=filename,
                language="nan-TW",
            )
        whisper_language = "zh" if requested_language == "zh-TW" else None
        return await self.whisper.transcribe(
            audio_bytes=audio_bytes,
            filename=filename,
            language=whisper_language,
        )


def _with_requested_language(
    transcription: WhisperTranscription,
    requested_language: str,
) -> WhisperTranscription:
    if transcription.requested_language == requested_language:
        return transcription
    return WhisperTranscription(
        text=transcription.text,
        language=transcription.language,
        language_probability=transcription.language_probability,
        duration_seconds=transcription.duration_seconds,
        duration_after_vad_seconds=transcription.duration_after_vad_seconds,
        segment_count=transcription.segment_count,
        model=transcription.model,
        provider=transcription.provider,
        requested_language=requested_language,
    )
