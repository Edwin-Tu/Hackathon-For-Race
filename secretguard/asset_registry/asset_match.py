"""資產比對結果結構，供各比對器（matcher）共用（F13 一、四）。"""

from __future__ import annotations

from dataclasses import dataclass

from secretguard.common.enums import ProtectionMode


@dataclass
class AssetMatch:
    """單筆資產命中結果。"""

    asset_id: str
    asset_name: str
    match_type: str
    risk_level: str
    matched_text: str = ""
    confidence: float = 1.0
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "asset_name": self.asset_name,
            "match_type": self.match_type,
            "risk_level": self.risk_level,
            "matched": bool(self.matched_text),
            "matched_length": len(self.matched_text),
            "confidence": self.confidence,
            "reason": self.reason,
        }


EXACT = ProtectionMode.EXACT_MATCH.value
CASE_INSENSITIVE = ProtectionMode.CASE_INSENSITIVE_MATCH.value
ALIAS = ProtectionMode.ALIAS_MATCH.value
PARTIAL = ProtectionMode.PARTIAL_MATCH.value
ENCODING = ProtectionMode.ENCODING_MATCH.value
SEMANTIC = ProtectionMode.SEMANTIC_MATCH.value
TRANSLATION = ProtectionMode.TRANSLATION_MATCH.value
RECONSTRUCTION = ProtectionMode.RECONSTRUCTION_MATCH.value
