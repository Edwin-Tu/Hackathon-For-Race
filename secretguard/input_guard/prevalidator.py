"""Resource and type validation performed before regex or decoding work."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass


class InputValidationError(ValueError):
    """Typed validation error that callers can safely map to a blocked request."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class InputLimits:
    max_input_chars: int = 16_000
    max_control_char_ratio: float = 0.05
    max_nul_chars: int = 0


class InputPreValidator:
    def __init__(self, limits: InputLimits | None = None) -> None:
        self.limits = limits or InputLimits()

    def validate(self, text: str) -> str:
        if not isinstance(text, str):
            raise InputValidationError("input_not_string", "Input must be a string.")
        if not text.strip():
            raise InputValidationError("input_empty", "Input must not be empty.")
        if len(text) > self.limits.max_input_chars:
            raise InputValidationError("input_too_long", "Input exceeds the character limit.")
        if text.count("\x00") > self.limits.max_nul_chars:
            raise InputValidationError("nul_character_detected", "NUL characters are not allowed.")

        controls = 0
        for char in text:
            if char in "\n\r\t":
                continue
            if unicodedata.category(char) in {"Cc", "Cf"}:
                controls += 1
        ratio = controls / max(len(text), 1)
        if ratio > self.limits.max_control_char_ratio:
            raise InputValidationError(
                "excessive_control_characters",
                "Input contains too many control or formatting characters.",
            )
        return text
