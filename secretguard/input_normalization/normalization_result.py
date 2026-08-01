"""Normalization result and redacted transformation metadata."""

from __future__ import annotations

from dataclasses import dataclass, field


class SuspicionFlag:
    UNICODE_CONFUSABLE_DETECTED = "unicode_confusable_detected"
    ZERO_WIDTH_CHARACTER_REMOVED = "zero_width_character_removed"
    SPACING_OBFUSCATION_DETECTED = "spacing_obfuscation_detected"
    SYMBOL_OBFUSCATION_DETECTED = "symbol_obfuscation_detected"
    BASE64_CANDIDATE_DETECTED = "base64_candidate_detected"
    HEX_CANDIDATE_DETECTED = "hex_candidate_detected"
    URL_ENCODING_CANDIDATE_DETECTED = "url_encoding_candidate_detected"
    CROSS_LANGUAGE_ALIAS_DETECTED = "cross_language_alias_detected"
    RECONSTRUCTION_PATTERN_DETECTED = "reconstruction_pattern_detected"
    ROLE_CLAIM_DETECTED = "role_claim_detected"


@dataclass
class Transformation:
    """A safe, non-reversible record of a normalization change."""

    type: str
    changed: bool = True
    source_length: int = 0
    result_length: int = 0
    changed_character_count: int = 0

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "changed": self.changed,
            "source_length": self.source_length,
            "result_length": self.result_length,
            "changed_character_count": self.changed_character_count,
        }


@dataclass
class NormalizationResult:
    raw_text: str
    normalized_text: str = ""
    casefold_text: str = ""
    compact_text: str = ""
    symbol_stripped_text: str = ""
    decoded_candidates: list[str] = field(default_factory=list)
    detected_languages: list[str] = field(default_factory=list)
    matched_aliases: list[str] = field(default_factory=list)
    suspicion_flags: list[str] = field(default_factory=list)
    transformations: list[Transformation] = field(default_factory=list)

    def add_flag(self, flag: str) -> None:
        if flag not in self.suspicion_flags:
            self.suspicion_flags.append(flag)

    def add_transformation(self, type_: str, from_: str, to: str, text: str = "") -> None:
        # Keep the legacy call signature, but never retain the original or transformed text.
        changed_count = abs(len(from_) - len(to))
        if len(from_) == len(to):
            changed_count = sum(1 for a, b in zip(from_, to) if a != b)
        self.transformations.append(
            Transformation(
                type=type_,
                changed=from_ != to,
                source_length=len(from_),
                result_length=len(to),
                changed_character_count=changed_count,
            )
        )

    def detection_views(self) -> list[tuple[str, str]]:
        """Return deduplicated views intended only for detection."""

        candidates = [
            ("normalized", self.normalized_text),
            ("casefold", self.casefold_text),
            ("symbol_stripped", self.symbol_stripped_text),
            *(('decoded', value) for value in self.decoded_candidates),
        ]
        seen: set[str] = set()
        views: list[tuple[str, str]] = []
        for name, value in candidates:
            if value and value not in seen:
                seen.add(value)
                views.append((name, value))
        return views

    def to_dict(self, include_text: bool = False, include_raw_text: bool = False) -> dict:
        # Text views are omitted by default because normalized or encoded input may itself
        # contain protected data. Callers must opt in explicitly for transient debugging.
        result = {
            "decoded_candidate_count": len(self.decoded_candidates),
            "detected_languages": self.detected_languages,
            "matched_aliases": self.matched_aliases,
            "suspicion_flags": self.suspicion_flags,
            "transformations": [t.to_dict() for t in self.transformations],
        }
        if include_text:
            result.update({
                "normalized_text": self.normalized_text,
                "casefold_text": self.casefold_text,
                "compact_text": self.compact_text,
                "symbol_stripped_text": self.symbol_stripped_text,
            })
        if include_raw_text:
            result["raw_text"] = self.raw_text
        return result
