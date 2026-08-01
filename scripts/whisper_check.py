"""Load faster-whisper or transcribe one local audio file."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from app.config import settings
from app.whisper_service import WhisperService


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", nargs="?", help="Audio file to transcribe")
    parser.add_argument("--load-model", action="store_true")
    parser.add_argument("--language", default=None)
    args = parser.parse_args()

    service = WhisperService(
        enabled=settings.WHISPER_ENABLED,
        model_size=settings.WHISPER_MODEL_SIZE,
        device=settings.WHISPER_DEVICE,
        compute_type=settings.WHISPER_COMPUTE_TYPE,
        download_root=settings.WHISPER_DOWNLOAD_ROOT,
        beam_size=settings.WHISPER_BEAM_SIZE,
        vad_filter=settings.WHISPER_VAD_FILTER,
    )

    if args.load_model:
        await service.load_model()
        print(
            f"[PASS] loaded model={service.model_size} "
            f"device={service.device} compute_type={service.compute_type}"
        )
        if not args.audio:
            return

    if not args.audio:
        parser.error("Provide an audio file or use --load-model")

    path = Path(args.audio)
    result = await service.transcribe(
        audio_bytes=path.read_bytes(),
        filename=path.name,
        language=args.language,
    )
    print(f"text={result.text}")
    print(f"language={result.language} probability={result.language_probability}")
    print(
        f"duration={result.duration_seconds} "
        f"duration_after_vad={result.duration_after_vad_seconds} "
        f"segments={result.segment_count} model={result.model}"
    )


if __name__ == "__main__":
    asyncio.run(main())
