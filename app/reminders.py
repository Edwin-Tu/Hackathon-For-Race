"""Reminder scheduler, atomic claim loop, local alarm, and local speech output."""

from __future__ import annotations

import asyncio
import logging
import os
import platform
import shutil
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.output import DeliveryResult, OutputAdapter, OutputEnvelope
from app.repositories.base import CareRepository, Reminder

logger = logging.getLogger(__name__)
UTC = timezone.utc


class LocalAlarmPlayer:
    """Play a short local notification sound with graceful fallback."""

    def __init__(self, *, enabled: bool = True, sound_file: str | None = None) -> None:
        self._enabled = enabled
        self._sound_file = sound_file

    @property
    def backend(self) -> str:
        if not self._enabled:
            return "audio_disabled"
        system = platform.system().lower()
        if system == "darwin" and shutil.which("afplay"):
            return "macos_afplay"
        if system == "windows":
            return "windows_winsound"
        if shutil.which("paplay"):
            return "linux_paplay"
        if shutil.which("aplay"):
            return "linux_aplay"
        if shutil.which("ffplay"):
            return "ffplay"
        return "terminal_bell"

    def play(self) -> DeliveryResult:
        backend = self.backend
        if backend == "audio_disabled":
            return DeliveryResult(ok=True, backend=backend)

        try:
            if backend == "macos_afplay":
                default_sound = "/System/Library/Sounds/Glass.aiff"
                sound = self._sound_file or default_sound
                if not Path(sound).is_file():
                    raise FileNotFoundError(sound)
                subprocess.run(
                    ["afplay", sound],
                    check=True,
                    timeout=10,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif backend == "windows_winsound":
                import winsound  # type: ignore[import-not-found]

                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            elif backend == "linux_paplay":
                sound = self._sound_file or "/usr/share/sounds/freedesktop/stereo/complete.oga"
                subprocess.run(["paplay", sound], check=True, timeout=10)
            elif backend == "linux_aplay":
                sound = self._sound_file or "/usr/share/sounds/alsa/Front_Center.wav"
                subprocess.run(["aplay", sound], check=True, timeout=10)
            elif backend == "ffplay":
                if not self._sound_file:
                    raise FileNotFoundError("LOCAL_ALARM_SOUND_FILE is required for ffplay")
                subprocess.run(
                    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", self._sound_file],
                    check=True,
                    timeout=10,
                )
            else:
                print("\a", end="", flush=True)
            return DeliveryResult(ok=True, backend=backend)
        except Exception as exc:
            logger.warning("Local alarm failed (%s): %s", backend, exc)
            print("\a", end="", flush=True)
            return DeliveryResult(ok=True, backend=f"{backend}+terminal_bell", error=str(exc))


class LocalSpeechPlayer:
    """Speak text using an operating-system command without shell interpolation."""

    def __init__(
        self,
        *,
        enabled: bool = True,
        voice: str | None = None,
        rate: int | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        self._enabled = enabled
        self._voice = voice
        self._rate = rate
        self._timeout_seconds = timeout_seconds

    @property
    def backend(self) -> str:
        if not self._enabled:
            return "tts_disabled"
        system = platform.system().lower()
        if system == "darwin" and shutil.which("say"):
            return "macos_say"
        if system == "windows" and shutil.which("powershell"):
            return "windows_sapi"
        if shutil.which("spd-say"):
            return "linux_spd_say"
        if shutil.which("espeak"):
            return "linux_espeak"
        return "tts_unavailable"

    def speak(self, text: str) -> DeliveryResult:
        text = " ".join(text.split())[:1000]
        backend = self.backend
        if backend == "tts_disabled":
            return DeliveryResult(ok=True, backend=backend)
        if backend == "tts_unavailable":
            return DeliveryResult(ok=False, backend=backend, error="No local TTS backend")

        try:
            if backend == "macos_say":
                command = ["say"]
                if self._voice:
                    command.extend(["-v", self._voice])
                if self._rate:
                    command.extend(["-r", str(self._rate)])
                command.append(text)
            elif backend == "windows_sapi":
                escaped = text.replace("'", "''")
                script = (
                    "Add-Type -AssemblyName System.Speech; "
                    "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    f"$s.Speak('{escaped}')"
                )
                command = ["powershell", "-NoProfile", "-Command", script]
            elif backend == "linux_spd_say":
                command = ["spd-say", "--wait", text]
            else:
                command = ["espeak", text]

            subprocess.run(
                command,
                check=True,
                timeout=self._timeout_seconds,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return DeliveryResult(ok=True, backend=backend)
        except Exception as exc:
            logger.warning("Local speech failed (%s): %s", backend, exc)
            return DeliveryResult(ok=False, backend=backend, error=str(exc))


class LocalReminderOutputAdapter:
    """Serialize alarm + TTS delivery so reminders do not speak over each other."""

    backend = "local_alarm_tts"

    def __init__(
        self,
        alarm: LocalAlarmPlayer,
        speech: LocalSpeechPlayer,
    ) -> None:
        self._alarm = alarm
        self._speech = speech
        self._lock = threading.Lock()

    @property
    def alarm_backend(self) -> str:
        return self._alarm.backend

    @property
    def speech_backend(self) -> str:
        return self._speech.backend

    def emit(self, envelope: OutputEnvelope) -> DeliveryResult:
        with self._lock:
            alarm_result = self._alarm.play()
            speech_result = self._speech.speak(envelope.speech_text)

        ok = alarm_result.ok or speech_result.ok
        errors = [
            result.error
            for result in (alarm_result, speech_result)
            if result.error
        ]
        return DeliveryResult(
            ok=ok,
            backend=f"{alarm_result.backend}+{speech_result.backend}",
            error="; ".join(errors) if errors else None,
        )


@dataclass(frozen=True)
class ReminderRunResult:
    reminder_id: str
    status: str
    backend: str | None = None
    error: str | None = None


class ReminderScheduler:
    """Poll, atomically claim, deliver, and finalize due reminders."""

    def __init__(
        self,
        *,
        repository: CareRepository,
        output_adapter: OutputAdapter,
        poll_seconds: float = 2.0,
        batch_size: int = 20,
        missed_after_seconds: int = 3600,
        stale_claim_seconds: int = 120,
    ) -> None:
        self._repository = repository
        self._output_adapter = output_adapter
        self._poll_seconds = max(0.25, poll_seconds)
        self._batch_size = max(1, batch_size)
        self._missed_after_seconds = max(0, missed_after_seconds)
        self._stale_claim_seconds = max(10, stale_claim_seconds)
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._run_lock = asyncio.Lock()
        self._last_run_at: datetime | None = None
        self._last_error: str | None = None

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    def status(self) -> dict[str, object]:
        return {
            "running": self.running,
            "poll_seconds": self._poll_seconds,
            "batch_size": self._batch_size,
            "missed_after_seconds": self._missed_after_seconds,
            "last_run_at": self._last_run_at.isoformat() if self._last_run_at else None,
            "last_error": self._last_error,
        }

    async def start(self) -> None:
        if self.running:
            return
        self._stop_event = asyncio.Event()
        stale_before = datetime.now(UTC) - timedelta(seconds=self._stale_claim_seconds)
        try:
            recovered = await asyncio.to_thread(
                self._repository.recover_stale_reminders,
                stale_before=stale_before,
            )
            if recovered:
                logger.warning("Recovered %s stale reminder claim(s)", recovered)
        except Exception:
            logger.exception("Unable to recover stale reminders")
        self._task = asyncio.create_task(self._loop(), name="reminder-scheduler")
        logger.info("Reminder scheduler started")

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is not None:
            await self._task
        self._task = None
        logger.info("Reminder scheduler stopped")

    async def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self.run_once()
            except Exception as exc:  # pragma: no cover - background safety net
                self._last_error = str(exc)
                logger.exception("Reminder scheduler iteration failed")
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._poll_seconds)
            except TimeoutError:
                pass

    async def run_once(self, *, now: datetime | None = None) -> list[ReminderRunResult]:
        async with self._run_lock:
            current = now or datetime.now(UTC)
            if current.tzinfo is None:
                raise ValueError("now must include timezone information")
            self._last_run_at = current
            self._last_error = None

            reminders = await asyncio.to_thread(
                self._repository.claim_due_reminders,
                current,
                limit=self._batch_size,
                missed_after_seconds=self._missed_after_seconds,
            )

            results: list[ReminderRunResult] = []
            for reminder in reminders:
                results.append(await self._deliver(reminder, current))
            return results

    async def _deliver(
        self,
        reminder: Reminder,
        triggered_at: datetime,
    ) -> ReminderRunResult:
        envelope = OutputEnvelope(
            event_type="reminder.triggered",
            persona_id=reminder.persona_id,
            display_text=f"提醒已觸發：{reminder.title}",
            speech_text=f"提醒您，現在該{reminder.title}了。",
            source_id=reminder.record_id,
            metadata={
                "importance": reminder.importance,
                "scheduled_at": reminder.scheduled_at.isoformat(),
            },
        )

        delivery = await asyncio.to_thread(self._output_adapter.emit, envelope)
        if delivery.ok:
            updated = await asyncio.to_thread(
                self._repository.mark_reminder_triggered,
                reminder.record_id,
                triggered_at=triggered_at,
            )
            if not updated:
                error = "Reminder status changed before finalization"
                logger.error("%s: %s", reminder.record_id, error)
                return ReminderRunResult(
                    reminder_id=reminder.record_id,
                    status="failed",
                    backend=delivery.backend,
                    error=error,
                )
            return ReminderRunResult(
                reminder_id=reminder.record_id,
                status="triggered",
                backend=delivery.backend,
                error=delivery.error,
            )

        await asyncio.to_thread(
            self._repository.mark_reminder_failed,
            reminder.record_id,
            failed_at=triggered_at,
        )
        return ReminderRunResult(
            reminder_id=reminder.record_id,
            status="failed",
            backend=delivery.backend,
            error=delivery.error,
        )
