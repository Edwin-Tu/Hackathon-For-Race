"""Smoke-test the bilingual voice endpoint with a real audio file."""

from __future__ import annotations

import argparse
import json
import mimetypes
from pathlib import Path

import httpx


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("audio_file", type=Path)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--token", default="")
    parser.add_argument("--language", choices=("zh-TW", "nan-TW"), required=True)
    parser.add_argument("--session-id", default="bilingual-smoke")
    args = parser.parse_args()

    if not args.audio_file.is_file():
        raise SystemExit(f"Audio file not found: {args.audio_file}")

    headers = {}
    if args.token:
        headers["Authorization"] = f"Bearer {args.token}"

    mime_type = mimetypes.guess_type(args.audio_file.name)[0] or "application/octet-stream"
    with args.audio_file.open("rb") as audio:
        response = httpx.post(
            f"{args.base_url.rstrip('/')}/api/voice/turn",
            headers=headers,
            files={"audio": (args.audio_file.name, audio, mime_type)},
            data={"language": args.language, "session_id": args.session_id},
            timeout=180,
        )

    print(f"HTTP {response.status_code}")
    try:
        payload = response.json()
    except ValueError:
        print(response.text)
        raise SystemExit(1)

    # Do not dump the base64 audio body into the terminal.
    speech = payload.get("speech_delivery") or {}
    if speech.get("audio_base64"):
        speech["audio_base64"] = f"<base64 {len(speech['audio_base64'])} chars>"
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if response.status_code != 200:
        raise SystemExit(1)
    expected_provider = "breeze" if args.language == "nan-TW" else "faster_whisper"
    actual_provider = payload.get("trace", {}).get("provider")
    if args.language == "nan-TW" and actual_provider not in {"breeze", "faster_whisper"}:
        raise SystemExit(f"Unexpected ASR provider: {actual_provider}")
    if args.language == "zh-TW" and actual_provider != expected_provider:
        raise SystemExit(f"Expected {expected_provider}, got {actual_provider}")
    if not payload.get("agent", {}).get("reply"):
        raise SystemExit("Agent reply is empty")


if __name__ == "__main__":
    main()
