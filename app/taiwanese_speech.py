"""Faithful Agent-reply translation and optional Taiwanese speech synthesis."""

from __future__ import annotations

import asyncio
import io
import json
import logging
import re
import threading
import wave
from array import array
from dataclasses import dataclass
from typing import Any, Callable

from app.models import ProviderResponse
from app.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)

TRANSLATION_SYSTEM_PROMPT = """你是臺灣台語翻譯器。只翻譯，不回答問題、不增刪資訊、不改變事實。
請把使用者提供的完整中文回覆忠實翻成臺灣台語，保留原句中的數字、時間、日期、劑量、人名、藥名、record_id 與否定語意。
輸出必須是單一 JSON 物件，不得加入 Markdown 或說明：
{"display_text":"台語漢字完整翻譯","tts_text":"同一句的臺羅或白話字羅馬字，使用可供閩南語 TTS 發音的拉丁字母與聲調符號"}
若原文含有程式碼、URL、UUID 或英文字詞，原樣保留在兩個欄位中。"""


class TaiwaneseTranslationError(RuntimeError):
    """Raised when a faithful Taiwanese translation cannot be produced."""


class TaiwaneseTTSUnavailableError(RuntimeError):
    """Raised when the optional Taiwanese TTS provider is unavailable."""


@dataclass(frozen=True)
class TaiwaneseTranslation:
    display_text: str
    tts_text: str
    model: str


@dataclass(frozen=True)
class SynthesizedSpeech:
    audio_bytes: bytes
    content_type: str
    sample_rate_hz: int
    model: str


class TaiwaneseReplyTranslator:
    """Use the configured LLM to translate the Agent reply verbatim."""

    def __init__(self, provider: BaseLLMProvider) -> None:
        self._provider = provider

    async def translate(self, agent_reply: str) -> TaiwaneseTranslation:
        normalized = " ".join(agent_reply.split())
        if not normalized:
            raise TaiwaneseTranslationError("Agent 回覆為空，無法翻譯")

        response = await self._provider.chat(
            messages=[{"role": "user", "content": normalized}],
            system_prompt=TRANSLATION_SYSTEM_PROMPT,
            tool_config=None,
        )
        if not response.success:
            raise TaiwaneseTranslationError(
                response.error_message or "台語翻譯模型呼叫失敗"
            )

        payload = _parse_translation_json(response.text)
        display_text = str(payload.get("display_text", "")).strip()
        tts_text = str(payload.get("tts_text", "")).strip()
        if not display_text or not tts_text:
            raise TaiwaneseTranslationError("台語翻譯缺少 display_text 或 tts_text")
        _validate_preserved_literals(normalized, display_text, tts_text)
        return TaiwaneseTranslation(
            display_text=display_text,
            tts_text=tts_text,
            model=response.model,
        )


def _parse_translation_json(text: str) -> dict[str, Any]:
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*", "", candidate)
        candidate = re.sub(r"\s*```$", "", candidate)
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start < 0 or end < start:
        raise TaiwaneseTranslationError("台語翻譯沒有回傳 JSON")
    try:
        value = json.loads(candidate[start : end + 1])
    except json.JSONDecodeError as exc:
        raise TaiwaneseTranslationError("台語翻譯 JSON 格式錯誤") from exc
    if not isinstance(value, dict):
        raise TaiwaneseTranslationError("台語翻譯回傳格式錯誤")
    return value


def _validate_preserved_literals(original: str, *translations: str) -> None:
    """Reject translations that drop high-risk literal values.

    Only stable literals are checked here. Natural-language words are allowed
    to change because the requested operation is translation.
    """

    protected = set(
        re.findall(
            r"(?:\b\d{1,4}(?::\d{2})?\b|\b[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}\b|https?://\S+|\b[A-Za-z][A-Za-z0-9._/-]*\b)",
            original,
            flags=re.IGNORECASE,
        )
    )
    combined = " ".join(translations)
    missing = [literal for literal in protected if literal not in combined]
    if missing:
        raise TaiwaneseTranslationError("台語翻譯遺失必要的數字或識別值")


TokenizerFactory = Callable[[str], Any]
ModelFactory = Callable[[str], Any]


class TaiwaneseTTSService:
    """Lazy MMS Min Nan TTS service returning browser-playable WAV audio."""

    def __init__(
        self,
        *,
        enabled: bool = False,
        model_id: str = "facebook/mms-tts-nan",
        device: str = "auto",
        max_chars: int = 600,
        tokenizer_factory: TokenizerFactory | None = None,
        model_factory: ModelFactory | None = None,
    ) -> None:
        self.enabled = enabled
        self.model_id = model_id
        self.device = device
        self.max_chars = max(1, max_chars)
        self._tokenizer_factory = tokenizer_factory
        self._model_factory = model_factory
        self._tokenizer: Any | None = None
        self._model: Any | None = None
        self._torch: Any | None = None
        self._resolved_device = "cpu"
        self._lock = threading.Lock()

    @property
    def loaded(self) -> bool:
        return self._model is not None and self._tokenizer is not None

    async def synthesize(self, text: str) -> SynthesizedSpeech:
        if not self.enabled:
            raise TaiwaneseTTSUnavailableError("台語 TTS is disabled")
        normalized = " ".join(text.split())
        if not normalized:
            raise TaiwaneseTTSUnavailableError("台語 TTS 文字為空")
        if len(normalized) > self.max_chars:
            raise TaiwaneseTTSUnavailableError("台語 TTS 文字超過長度上限")
        return await asyncio.to_thread(self._synthesize_sync, normalized)

    def _load(self) -> tuple[Any, Any, Any]:
        if self.loaded:
            return self._tokenizer, self._model, self._torch
        try:
            import torch
            from transformers import AutoTokenizer, VitsModel
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise TaiwaneseTTSUnavailableError(
                "台語 TTS 依賴尚未安裝，請執行：uv sync --extra bilingual-voice"
            ) from exc

        tokenizer_factory = self._tokenizer_factory or AutoTokenizer.from_pretrained
        model_factory = self._model_factory or VitsModel.from_pretrained
        try:
            tokenizer = tokenizer_factory(self.model_id)
            model = model_factory(self.model_id)
            resolved_device = _resolve_torch_device(torch, self.device)
            model = model.to(resolved_device)
            model.eval()
        except Exception as exc:
            raise TaiwaneseTTSUnavailableError(
                f"台語 TTS 模型載入失敗：{exc}"
            ) from exc

        self._tokenizer = tokenizer
        self._model = model
        self._torch = torch
        self._resolved_device = resolved_device
        return tokenizer, model, torch

    def _synthesize_sync(self, text: str) -> SynthesizedSpeech:
        with self._lock:
            tokenizer, model, torch = self._load()
            inputs = tokenizer(text, return_tensors="pt")
            inputs = {
                key: value.to(self._resolved_device)
                for key, value in inputs.items()
            }
            with torch.no_grad():
                output = model(**inputs).waveform
            waveform = output.squeeze().detach().to("cpu").float().tolist()
            sample_rate = int(getattr(model.config, "sampling_rate", 16000))

        audio_bytes = _float_waveform_to_wav(waveform, sample_rate)
        return SynthesizedSpeech(
            audio_bytes=audio_bytes,
            content_type="audio/wav",
            sample_rate_hz=sample_rate,
            model=self.model_id,
        )


def _resolve_torch_device(torch: Any, requested: str) -> str:
    normalized = requested.strip().lower()
    if normalized == "auto":
        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"
    if normalized in {"cpu", "cuda", "mps"}:
        return normalized
    raise TaiwaneseTTSUnavailableError(f"不支援的台語 TTS device：{requested}")


def _float_waveform_to_wav(samples: list[float], sample_rate: int) -> bytes:
    pcm = array(
        "h",
        (
            int(max(-1.0, min(1.0, float(sample))) * 32767)
            for sample in samples
        ),
    )
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm.tobytes())
    return buffer.getvalue()
