"""Policy context for the Input Guard decision engine."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PolicyContext:
    normalized_prompt: str
    attack_category: str | None = None
    risk_score: int = 0
    risk_level: str = "low"
    attack_risk_score: int = 0
    access_risk_score: int = 0
    matched_assets: list[dict] = field(default_factory=list)
    user_role: str = "guest"
    is_authorized: bool = False
    authorization_status: str = "unknown"
    session_risk_score: int = 0
    input_guard_flags: list[str] = field(default_factory=list)
    classifier_confidence: float = 0.0
    history_flags: list[str] = field(default_factory=list)
    operation: str | None = None
    scope: str | None = None
    disclosure_mode: str | None = None
    asset_reference_type: str | None = None
    is_attack: bool = False
    is_suspicious: bool = False
    cross_scope_request: bool = False
