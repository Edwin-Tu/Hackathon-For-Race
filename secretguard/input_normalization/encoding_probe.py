"""Bounded Base64, hex and URL-encoding candidate detection."""

from __future__ import annotations

import base64
import binascii
import re
import urllib.parse

from secretguard.input_normalization.normalization_result import NormalizationResult, SuspicionFlag

MAX_DECODED_LENGTH = 4096
MAX_DECODE_CANDIDATES = 5
MAX_TOKEN_LENGTH = 8192

_BASE64_PATTERN = re.compile(r"^[A-Za-z0-9+/_-]{8,}={0,2}$")
_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]{8,}$")
_URL_ENCODED_PATTERN = re.compile(r"%[0-9a-fA-F]{2}")


def _safe_text(decoded: bytes) -> str | None:
    if len(decoded) > MAX_DECODED_LENGTH:
        return None
    try:
        text = decoded.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None
    if not text or len(text) > MAX_DECODED_LENGTH:
        return None
    printable_ratio = sum(ch.isprintable() or ch in "\r\n\t" for ch in text) / len(text)
    return text if printable_ratio >= 0.85 else None


def _try_base64(candidate: str) -> str | None:
    if len(candidate) > MAX_TOKEN_LENGTH or not _BASE64_PATTERN.fullmatch(candidate):
        return None
    try:
        padded = candidate + "=" * (-len(candidate) % 4)
        return _safe_text(base64.b64decode(padded, validate=False))
    except (binascii.Error, ValueError):
        return None


def _try_hex(candidate: str) -> str | None:
    if len(candidate) > MAX_TOKEN_LENGTH or not _HEX_PATTERN.fullmatch(candidate) or len(candidate) % 2:
        return None
    try:
        return _safe_text(bytes.fromhex(candidate))
    except ValueError:
        return None


def _try_url_decode(text: str) -> str | None:
    if len(text) > MAX_TOKEN_LENGTH or not _URL_ENCODED_PATTERN.search(text):
        return None
    decoded = urllib.parse.unquote(text)
    if decoded == text or len(decoded) > MAX_DECODED_LENGTH:
        return None
    return decoded


def apply(result: NormalizationResult, text: str) -> list[str]:
    candidates: list[str] = []
    tokens = [text] + text.split() + re.split(r"[^A-Za-z0-9+/_=-]+", text)
    seen_tokens: set[str] = set()

    for token in tokens:
        if not token or token in seen_tokens or len(candidates) >= MAX_DECODE_CANDIDATES:
            continue
        seen_tokens.add(token)

        b64 = _try_base64(token)
        if b64:
            result.add_flag(SuspicionFlag.BASE64_CANDIDATE_DETECTED)
            result.add_transformation(SuspicionFlag.BASE64_CANDIDATE_DETECTED, token, b64)
            candidates.append(b64)
            if len(candidates) >= MAX_DECODE_CANDIDATES:
                break

        hex_decoded = _try_hex(token)
        if hex_decoded and hex_decoded not in candidates:
            result.add_flag(SuspicionFlag.HEX_CANDIDATE_DETECTED)
            result.add_transformation(SuspicionFlag.HEX_CANDIDATE_DETECTED, token, hex_decoded)
            candidates.append(hex_decoded)

    if len(candidates) < MAX_DECODE_CANDIDATES:
        url_decoded = _try_url_decode(text)
        if url_decoded and url_decoded not in candidates:
            result.add_flag(SuspicionFlag.URL_ENCODING_CANDIDATE_DETECTED)
            result.add_transformation(SuspicionFlag.URL_ENCODING_CANDIDATE_DETECTED, text, url_decoded)
            candidates.append(url_decoded)

    return candidates[:MAX_DECODE_CANDIDATES]
