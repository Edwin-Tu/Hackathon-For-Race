"""FastAPI application entry point."""

from __future__ import annotations

import asyncio
import base64
import logging
import secrets
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.models import (
    ChatRequest,
    ChatResponse,
    ConfirmationRequest,
    HealthResponse,
    InputGuardCheckRequest,
    InputGuardCheckResponse,
    OutputEventResponse,
    ReminderRunItem,
    ReminderRunResponse,
    SpeechDeliveryTrace,
    TranscriptionResponse,
    TranscriptionTrace,
    VoiceConfirmationRequest,
    VoiceReplyResponse,
    VoiceTurnResponse,
)
from app.output import (
    CompositeOutputAdapter,
    ConsoleOutputAdapter,
    OutputEnvelope,
    OutputEventStore,
    StoreOutputAdapter,
)
from app.breeze_asr_service import BreezeASRService
from app.hybrid_asr_service import (
    HybridASRService,
    is_taiwanese_language,
    normalize_voice_language,
)
from app.providers.bedrock import BedrockProvider
from app.reminders import (
    LocalAlarmPlayer,
    LocalReminderOutputAdapter,
    LocalSpeechPlayer,
    ReminderScheduler,
)
from app.repositories import create_care_repository
from app.security import AgentInputGuard
from app.services.agent_service import AgentService
from app.taiwanese_speech import (
    TaiwaneseReplyTranslator,
    TaiwaneseTTSService,
    TaiwaneseTranslationError,
    TaiwaneseTTSUnavailableError,
)
from app.tools import DemoAuthContextFactory, ToolGateway
from app.whisper_service import (
    EmptyTranscriptionError,
    WhisperService,
    WhisperUnavailableError,
)

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

provider = BedrockProvider()
repository = create_care_repository()
gateway = ToolGateway(repository=repository)
input_guard = AgentInputGuard(
    enabled=settings.INPUT_GUARD_ENABLED,
    fail_closed=settings.INPUT_GUARD_FAIL_CLOSED,
)
agent_service = AgentService(
    provider=provider,
    gateway=gateway,
    input_guard=input_guard,
    repository=repository,
)

output_store = OutputEventStore(max_events=settings.OUTPUT_EVENT_BUFFER_SIZE)
local_alarm_player = LocalAlarmPlayer(
    enabled=settings.LOCAL_ALARM_ENABLED,
    sound_file=settings.LOCAL_ALARM_SOUND_FILE,
)
local_speech_player = LocalSpeechPlayer(
    enabled=settings.LOCAL_TTS_ENABLED,
    voice=settings.LOCAL_TTS_VOICE,
    rate=settings.LOCAL_TTS_RATE,
)
local_output = LocalReminderOutputAdapter(
    alarm=local_alarm_player,
    speech=local_speech_player,
)
output_adapter = CompositeOutputAdapter(
    StoreOutputAdapter(output_store),
    ConsoleOutputAdapter(),
    local_output,
)
reminder_scheduler = ReminderScheduler(
    repository=repository,
    output_adapter=output_adapter,
    poll_seconds=settings.REMINDER_POLL_SECONDS,
    batch_size=settings.REMINDER_BATCH_SIZE,
    missed_after_seconds=settings.REMINDER_MISSED_AFTER_SECONDS,
    stale_claim_seconds=settings.REMINDER_STALE_CLAIM_SECONDS,
)
mandarin_whisper_service = WhisperService(
    enabled=settings.WHISPER_ENABLED,
    model_size=settings.WHISPER_MODEL_SIZE,
    device=settings.WHISPER_DEVICE,
    compute_type=settings.WHISPER_COMPUTE_TYPE,
    download_root=settings.WHISPER_DOWNLOAD_ROOT,
    beam_size=settings.WHISPER_BEAM_SIZE,
    vad_filter=settings.WHISPER_VAD_FILTER,
)
breeze_asr_service = BreezeASRService(
    enabled=settings.BREEZE_ASR_ENABLED,
    model_id=settings.BREEZE_ASR_MODEL_ID,
    device=settings.BREEZE_ASR_DEVICE,
)
# Keep the historical variable name for existing integrations/tests. It now
# routes Mandarin and Taiwanese requests to the correct ASR provider.
whisper_service = HybridASRService(
    whisper=mandarin_whisper_service,
    breeze=breeze_asr_service,
    mode=settings.ASR_MODE,
    auto_primary=settings.ASR_AUTO_PRIMARY,
    fallback_enabled=settings.ASR_FALLBACK_ENABLED,
)
taiwanese_reply_translator = TaiwaneseReplyTranslator(provider)
taiwanese_tts_service = TaiwaneseTTSService(
    enabled=settings.TAIWANESE_TTS_ENABLED,
    model_id=settings.TAIWANESE_TTS_MODEL_ID,
    device=settings.TAIWANESE_TTS_DEVICE,
    max_chars=settings.TAIWANESE_TTS_MAX_CHARS,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.REMINDER_SCHEDULER_ENABLED:
        await reminder_scheduler.start()
    try:
        yield
    finally:
        if reminder_scheduler.running:
            await reminder_scheduler.stop()


app = FastAPI(
    title="智慧長照語音 Agent",
    description="Input Guard、Agent、Tool Gateway、MySQL/RDS、中文/台語 ASR 與雙語語音輸出 API",
    version="0.8.0",
    lifespan=lifespan,
)


def _valid_api_bearer(request: Request) -> bool:
    expected = settings.api_bearer_token_value()
    if not expected:
        return False
    authorization = request.headers.get("authorization", "")
    scheme, _, supplied = authorization.partition(" ")
    return scheme.lower() == "bearer" and bool(supplied) and secrets.compare_digest(
        supplied, expected
    )


@app.middleware("http")
async def cloud_security_middleware(request: Request, call_next):
    """Protect public cloud demo APIs and attach baseline browser headers."""
    if settings.API_AUTH_ENABLED and request.url.path.startswith("/api/"):
        if not _valid_api_bearer(request):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid bearer token"},
                headers={"WWW-Authenticate": "Bearer"},
            )

    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), geolocation=(), payment=(), usb=()",
    )
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; "
        "object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
    )
    return response


if settings.API_AUTH_ENABLED and not settings.api_bearer_token_value():
    raise RuntimeError("API_AUTH_ENABLED=true requires API_BEARER_TOKEN")

DEMO_STATIC_DIR = Path(__file__).resolve().parent / "static" / "demo"
app.mount(
    "/demo-assets",
    StaticFiles(directory=DEMO_STATIC_DIR),
    name="demo-assets",
)


@app.get("/demo", include_in_schema=False, response_class=FileResponse)
@app.get("/demo/", include_in_schema=False, response_class=FileResponse)
async def validation_demo() -> FileResponse:
    """Serve the local validation console without an external UI build step."""
    return FileResponse(DEMO_STATIC_DIR / "index.html")


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_env=settings.APP_ENV,
        model_id=settings.BEDROCK_MODEL_ID,
        api_auth_required=settings.API_AUTH_ENABLED,
        repository_backend=settings.CARE_REPOSITORY_BACKEND,
        event_table=getattr(repository, "event_table", "memory"),
        asr_mode=settings.ASR_MODE,
        breeze_asr_enabled=settings.BREEZE_ASR_ENABLED,
        taiwanese_tts_enabled=settings.TAIWANESE_TTS_ENABLED,
    )


@app.post("/api/security/input-guard/check", response_model=InputGuardCheckResponse)
async def input_guard_check(
    request: InputGuardCheckRequest,
) -> InputGuardCheckResponse:
    """Inspect text without invoking Bedrock or any tool."""
    session_id = request.session_id or str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    auth_context = DemoAuthContextFactory.create_resident(
        requester_id=settings.DEMO_USER_ID,
        persona_id=settings.DEMO_PERSONA_ID,
        session_id=session_id,
        request_id=request_id,
    )
    outcome = input_guard.inspect(
        text=request.message,
        auth_context=auth_context,
    )
    return InputGuardCheckResponse(
        request_id=request_id,
        session_id=session_id,
        allowed=outcome.allowed,
        action=outcome.evidence.action,
        sanitized_text=outcome.sanitized_text if outcome.allowed else None,
        safe_response=outcome.safe_response,
        input_guard=outcome.evidence,
    )


@app.post("/api/agent/chat", response_model=ChatResponse)
async def agent_chat(request: ChatRequest) -> ChatResponse:
    return await agent_service.chat(request)


@app.post("/api/agent/confirm", response_model=ChatResponse)
async def agent_confirm(request: ConfirmationRequest) -> ChatResponse:
    """Confirm or cancel one pending server-side ToolCall without Bedrock."""
    return await agent_service.confirm(request)


@app.post("/api/voice/transcribe", response_model=TranscriptionResponse)
async def voice_transcribe(
    audio: UploadFile = File(...),
    language: str | None = Form(None),
) -> TranscriptionResponse:
    """Transcribe one audio upload locally without invoking the Agent."""
    transcription = await _transcribe_upload(audio, language=language)
    return TranscriptionResponse(
        transcript=transcription.text,
        trace=_trace_from_transcription(transcription),
    )


@app.post("/api/voice/turn", response_model=VoiceTurnResponse)
async def voice_turn(
    audio: UploadFile = File(...),
    session_id: str | None = Form(None),
    confirmation_token: str | None = Form(None),
    language: str | None = Form(None),
) -> VoiceTurnResponse:
    """Transcribe Mandarin/Taiwanese audio and run the guarded Agent pipeline."""
    transcription = await _transcribe_upload(audio, language=language)
    agent_response = await agent_service.chat(
        ChatRequest(
            message=transcription.text,
            session_id=session_id,
            confirmation_token=confirmation_token,
            input_type="voice",
        )
    )

    input_language = _resolved_input_language(language, transcription)
    translated_reply, reply_language, speech_delivery = await _prepare_voice_reply(
        agent_response=agent_response,
        input_language=input_language,
    )
    spoken_text = translated_reply or agent_response.reply

    if agent_response.reply:
        output_store.append(
            OutputEnvelope(
                event_type="agent.reply",
                persona_id=settings.DEMO_PERSONA_ID,
                display_text=translated_reply or agent_response.reply,
                speech_text=spoken_text,
                session_id=agent_response.session_id,
                metadata={
                    "source": "voice_turn",
                    "input_language": input_language,
                    "reply_language": reply_language,
                    "asr_provider": transcription.provider,
                },
            )
        )

    return VoiceTurnResponse(
        transcript=transcription.text,
        trace=_trace_from_transcription(transcription),
        agent=agent_response,
        input_language=input_language,
        reply_language=reply_language,
        translated_reply=translated_reply,
        speech_delivery=speech_delivery,
    )


@app.post("/api/voice/confirm", response_model=VoiceReplyResponse)
async def voice_confirm(request: VoiceConfirmationRequest) -> VoiceReplyResponse:
    """Confirm/cancel a pending voice ToolCall and preserve the reply language."""
    agent_response = await agent_service.confirm(
        ConfirmationRequest(
            session_id=request.session_id,
            confirmation_token=request.confirmation_token,
            decision=request.decision,
        )
    )
    input_language = normalize_voice_language(request.language)
    translated_reply, reply_language, speech_delivery = await _prepare_voice_reply(
        agent_response=agent_response,
        input_language=input_language,
    )
    return VoiceReplyResponse(
        agent=agent_response,
        reply_language=reply_language,
        translated_reply=translated_reply,
        speech_delivery=speech_delivery,
    )


async def _prepare_voice_reply(
    *,
    agent_response: ChatResponse,
    input_language: str,
) -> tuple[str | None, str, SpeechDeliveryTrace | None]:
    if not agent_response.reply:
        return None, "nan-TW" if is_taiwanese_language(input_language) else "zh-TW", None

    if is_taiwanese_language(input_language):
        translated_reply: str | None = None
        tts_text: str | None = None
        translation_error: str | None = None
        if settings.TAIWANESE_REPLY_TRANSLATION_ENABLED:
            try:
                translation = await taiwanese_reply_translator.translate(agent_response.reply)
                translated_reply = translation.display_text
                tts_text = translation.tts_text
            except TaiwaneseTranslationError as exc:
                translation_error = str(exc)
                logger.warning("Taiwanese reply translation failed: %s", exc)

        if translated_reply and tts_text and settings.TAIWANESE_TTS_ENABLED:
            try:
                speech = await taiwanese_tts_service.synthesize(tts_text)
                if len(speech.audio_bytes) > settings.MAX_TTS_AUDIO_BYTES:
                    raise TaiwaneseTTSUnavailableError("台語 TTS 音訊超過大小上限")
                return (
                    translated_reply,
                    "nan-TW",
                    SpeechDeliveryTrace(
                        ok=True,
                        backend=f"mms_tts:{speech.model}",
                        language="nan-TW",
                        spoken_text=translated_reply,
                        audio_base64=base64.b64encode(speech.audio_bytes).decode("ascii"),
                        content_type=speech.content_type,
                        sample_rate_hz=speech.sample_rate_hz,
                    ),
                )
            except TaiwaneseTTSUnavailableError as exc:
                logger.warning("Taiwanese TTS failed: %s", exc)
                return (
                    translated_reply,
                    "nan-TW",
                    SpeechDeliveryTrace(
                        ok=False,
                        backend="taiwanese_tts_unavailable",
                        error=str(exc),
                        language="nan-TW",
                        spoken_text=translated_reply,
                    ),
                )

        if translated_reply:
            return (
                translated_reply,
                "nan-TW",
                SpeechDeliveryTrace(
                    ok=False,
                    backend="taiwanese_tts_disabled",
                    error="台語 TTS 尚未啟用",
                    language="nan-TW",
                    spoken_text=translated_reply,
                ),
            )

        # Translation failure is non-fatal: keep the Agent reply and allow the
        # client to use its Mandarin fallback instead of fabricating Taiwanese.
        return (
            None,
            "zh-TW",
            SpeechDeliveryTrace(
                ok=False,
                backend="taiwanese_translation_failed",
                error=translation_error or "台語翻譯未啟用",
                language="zh-TW",
                spoken_text=agent_response.reply,
            ),
        )

    speech_delivery = None
    if settings.VOICE_TURN_LOCAL_TTS_ENABLED:
        result = await asyncio.to_thread(local_speech_player.speak, agent_response.reply)
        speech_delivery = SpeechDeliveryTrace(
            ok=result.ok,
            backend=result.backend,
            error=result.error,
            language="zh-TW",
            spoken_text=agent_response.reply,
        )
    return None, "zh-TW", speech_delivery


def _resolved_input_language(language: str | None, transcription) -> str:
    requested = normalize_voice_language(language or transcription.requested_language)
    if requested != "auto":
        return requested
    return normalize_voice_language(transcription.language)


@app.get("/api/reminders/status")
async def reminder_status() -> dict[str, object]:
    """Return scheduler runtime status without exposing reminder content."""
    return {
        "enabled": settings.REMINDER_SCHEDULER_ENABLED,
        **reminder_scheduler.status(),
        "local_alarm_backend": local_output.alarm_backend,
        "local_tts_backend": local_output.speech_backend,
    }


@app.post("/api/reminders/run-once", response_model=ReminderRunResponse)
async def reminder_run_once() -> ReminderRunResponse:
    """Development endpoint to trigger one scheduler poll immediately."""
    results = await reminder_scheduler.run_once()
    return ReminderRunResponse(
        processed=len(results),
        results=[
            ReminderRunItem(
                reminder_id=result.reminder_id,
                status=result.status,
                backend=result.backend,
                error=result.error,
            )
            for result in results
        ],
    )


@app.get("/api/output/events", response_model=list[OutputEventResponse])
async def output_events(
    after_id: int | None = Query(None, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session_id: str | None = Query(None, min_length=1, max_length=191),
) -> list[OutputEventResponse]:
    """Poll only events inside the current trusted demo persona/session scope."""
    return [
        OutputEventResponse(**event.to_dict())
        for event in output_store.list(
            after_id=after_id,
            limit=limit,
            persona_ids={settings.DEMO_PERSONA_ID},
            session_id=session_id,
        )
    ]


async def _transcribe_upload(audio: UploadFile, *, language: str | None):
    content_type = (audio.content_type or "").lower()
    filename = audio.filename or "voice.webm"
    suffix = Path(filename).suffix.lower()
    allowed_types = {
        "audio/wav",
        "audio/x-wav",
        "audio/mpeg",
        "audio/mp4",
        "audio/webm",
        "audio/ogg",
        "audio/flac",
        "application/ogg",
        "application/octet-stream",
    }
    allowed_suffixes = {".wav", ".mp3", ".m4a", ".mp4", ".webm", ".ogg", ".flac"}
    if content_type not in allowed_types and suffix not in allowed_suffixes:
        raise HTTPException(status_code=415, detail="不支援的音訊格式")

    audio_bytes = await audio.read(settings.MAX_AUDIO_BYTES + 1)
    if len(audio_bytes) > settings.MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="音訊檔案超過大小上限")
    if not audio_bytes:
        raise HTTPException(status_code=422, detail="音訊內容為空")

    try:
        return await whisper_service.transcribe(
            audio_bytes=audio_bytes,
            filename=filename,
            language=language,
        )
    except WhisperUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except EmptyTranscriptionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - runtime decoder/model failures
        logger.exception("Audio transcription failed")
        raise HTTPException(status_code=500, detail="語音轉錄失敗") from exc


def _trace_from_transcription(transcription) -> TranscriptionTrace:
    return TranscriptionTrace(
        model=transcription.model,
        provider=transcription.provider,
        requested_language=transcription.requested_language,
        language=transcription.language,
        language_probability=transcription.language_probability,
        duration_seconds=transcription.duration_seconds,
        duration_after_vad_seconds=transcription.duration_after_vad_seconds,
        segment_count=transcription.segment_count,
    )
