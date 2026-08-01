"""Public data contracts for the unified Input Guard service."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from secretguard.common.enums import PolicyAction


@dataclass(slots=True)
class InputGuardRequest:
    request_id: str
    session_id: str
    text: str
    user_id: str | None = None
    user_role: str = "guest"
    authorization_status: str = "unknown"
    authorization_scope: list[str] = field(default_factory=list)
    conversation_turn: int = 1
    session_signals: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RiskBreakdown:
    attack: int = 0
    asset: int = 0
    intent: int = 0
    session: int = 0
    obfuscation: int = 0
    access: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "attack": self.attack,
            "asset": self.asset,
            "intent": self.intent,
            "session": self.session,
            "obfuscation": self.obfuscation,
            "access": self.access,
        }


@dataclass(slots=True)
class InputGuardDecision:
    request_id: str
    session_id: str
    allowed: bool
    action: PolicyAction
    normalized_text: str
    sanitized_text: str | None
    attack_risk_score: int
    access_risk_score: int
    overall_risk_score: int
    overall_risk_level: str
    risk_breakdown: RiskBreakdown
    primary_category: str
    attack_categories: list[str]
    is_attack: bool
    is_suspicious: bool
    classifier_confidence: float
    matched_rules: list[str]
    suspicion_flags: list[str]
    matched_asset_ids: list[str]
    requires_authorization: bool
    strict_runtime_monitoring: bool
    reason_codes: list[str]
    safe_response: str | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "allowed": self.allowed,
            "action": self.action.value,
            "normalized_text": self.normalized_text,
            "sanitized_text": self.sanitized_text,
            "attack_risk_score": self.attack_risk_score,
            "access_risk_score": self.access_risk_score,
            "overall_risk_score": self.overall_risk_score,
            "overall_risk_level": self.overall_risk_level,
            "risk_breakdown": self.risk_breakdown.to_dict(),
            "primary_category": self.primary_category,
            "attack_categories": self.attack_categories,
            "is_attack": self.is_attack,
            "is_suspicious": self.is_suspicious,
            "classifier_confidence": self.classifier_confidence,
            "matched_rules": self.matched_rules,
            "suspicion_flags": self.suspicion_flags,
            "matched_asset_ids": self.matched_asset_ids,
            "requires_authorization": self.requires_authorization,
            "strict_runtime_monitoring": self.strict_runtime_monitoring,
            "reason_codes": self.reason_codes,
            "safe_response": self.safe_response,
            "metadata": self.metadata,
        }
