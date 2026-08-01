"""請求保護政策結構（F10 4.8：RequestProtectionPolicy）。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RequestProtectionPolicy:
    """請求保護政策（F10 4.8）。"""

    # 定位
    request_id: str
    action: str
    risk_score: int
    risk_level: str
    user_role: str
    attack_category: str | None = None

    # 資產
    protected_asset_ids: list[str] = field(default_factory=list)
    protected_asset_names: list[str] = field(default_factory=list)
    protected_asset_types: list[str] = field(default_factory=list)
    protection_modes: list[str] = field(default_factory=list)

    # 範圍
    allowed_response_scope: list[str] = field(default_factory=list)
    denied_response_scope: list[str] = field(default_factory=list)
    blocked_disclosure_types: list[str] = field(default_factory=list)

    # 技能
    enabled_skills: list[str] = field(default_factory=list)
    restricted_tokens: list[str] = field(default_factory=list)
    blocked_transformations: list[str] = field(default_factory=list)

    # 旗標
    require_authorization: bool = False
    runtime_monitoring_enabled: bool = False
    runtime_monitoring_mode: str = "low"
    interrupt_on_match: bool = False

    # 驗證
    output_verification_enabled: bool = False
    verify_exact: bool = True
    verify_partial: bool = True
    verify_encoding: bool = False
    verify_translation: bool = False
    verify_reconstruction: bool = False

    # 回應
    refusal_strategy: str = "polite_decline"
    safe_alternatives: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "action": self.action,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "user_role": self.user_role,
            "attack_category": self.attack_category,
            "protected_asset_ids": self.protected_asset_ids,
            "protected_asset_names": self.protected_asset_names,
            "protected_asset_types": self.protected_asset_types,
            "protection_modes": self.protection_modes,
            "allowed_response_scope": self.allowed_response_scope,
            "denied_response_scope": self.denied_response_scope,
            "blocked_disclosure_types": self.blocked_disclosure_types,
            "enabled_skills": self.enabled_skills,
            "restricted_tokens": self.restricted_tokens,
            "blocked_transformations": self.blocked_transformations,
            "require_authorization": self.require_authorization,
            "runtime_monitoring_enabled": self.runtime_monitoring_enabled,
            "runtime_monitoring_mode": self.runtime_monitoring_mode,
            "interrupt_on_match": self.interrupt_on_match,
            "output_verification_enabled": self.output_verification_enabled,
            "verify_exact": self.verify_exact,
            "verify_partial": self.verify_partial,
            "verify_encoding": self.verify_encoding,
            "verify_translation": self.verify_translation,
            "verify_reconstruction": self.verify_reconstruction,
            "refusal_strategy": self.refusal_strategy,
            "safe_alternatives": self.safe_alternatives,
            "metadata": self.metadata,
        }
