"""FastAPI application entry point."""

from __future__ import annotations

import asyncio
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
    VoiceTurnResponse,
)
from app.output import (
    CompositeOutputAdapter,
    ConsoleOutputAdapter,
    OutputEnvelope,
    OutputEventStore,
    StoreOutputAdapter,
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
whisper_service = WhisperService(
    enabled=settings.WHISPER_ENABLED,
    model_size=settings.WHISPER_MODEL_SIZE,
    device=settings.WHISPER_DEVICE,
    compute_type=settings.WHISPER_COMPUTE_TYPE,
    download_root=settings.WHISPER_DOWNLOAD_ROOT,
    beam_size=settings.WHISPER_BEAM_SIZE,
    vad_filter=settings.WHISPER_VAD_FILTER,
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
    description="Input Guard、Agent、Tool Gateway、MySQL/RDS、Whisper 與提醒輸出 API",
    version="0.7.0",
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
    """Transcribe audio, then run the normal guarded Agent pipeline."""
    transcription = await _transcribe_upload(audio, language=language)
    agent_response = await agent_service.chat(
        ChatRequest(
            message=transcription.text,
            session_id=session_id,
            confirmation_token=confirmation_token,
            input_type="voice",
        )
    )

    speech_delivery = None
    if agent_response.reply:
        output_store.append(
            OutputEnvelope(
                event_type="agent.reply",
                persona_id=settings.DEMO_PERSONA_ID,
                display_text=agent_response.reply,
                speech_text=agent_response.reply,
                session_id=agent_response.session_id,
                metadata={"source": "voice_turn"},
            )
        )
        if settings.VOICE_TURN_LOCAL_TTS_ENABLED:
            result = await asyncio.to_thread(
                local_speech_player.speak,
                agent_response.reply,
            )
            speech_delivery = SpeechDeliveryTrace(
                ok=result.ok,
                backend=result.backend,
                error=result.error,
            )

    return VoiceTurnResponse(
        transcript=transcription.text,
        trace=_trace_from_transcription(transcription),
        agent=agent_response,
        speech_delivery=speech_delivery,
    )


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
) -> list[OutputEventResponse]:
    """Poll reminder output events until a UI/WebSocket adapter is connected."""
    return [
        OutputEventResponse(**event.to_dict())
        for event in output_store.list(after_id=after_id, limit=limit)
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
        language=transcription.language,
        language_probability=transcription.language_probability,
        duration_seconds=transcription.duration_seconds,
        duration_after_vad_seconds=transcription.duration_after_vad_seconds,
        segment_count=transcription.segment_count,
    )
