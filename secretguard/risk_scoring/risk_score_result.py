"""Risk score result with separated attack and access risk."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RiskScoreResult:
    risk_score: int
    risk_level: str
    recommended_action: str
    attack_risk_score: int = 0
    access_risk_score: int = 0
    risk_breakdown: dict[str, int] = field(default_factory=dict)
    risk_factors: list[str] = field(default_factory=list)
    matched_assets: list[dict] = field(default_factory=list)
    triggered_rules: list[str] = field(default_factory=list)
    attack_category: str | None = None
    confidence: float | None = None
    requires_authorization: bool = False
    enable_strict_runtime_monitor: bool = False

    def to_dict(self) -> dict:
        return {
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "recommended_action": self.recommended_action,
            "attack_risk_score": self.attack_risk_score,
            "access_risk_score": self.access_risk_score,
            "risk_breakdown": self.risk_breakdown,
            "risk_factors": self.risk_factors,
            "matched_assets": self.matched_assets,
            "triggered_rules": self.triggered_rules,
            "attack_category": self.attack_category,
            "confidence": self.confidence,
            "requires_authorization": self.requires_authorization,
            "enable_strict_runtime_monitor": self.enable_strict_runtime_monitor,
        }

    def __getitem__(self, key: str):
        return self.to_dict()[key]

    def get(self, key: str, default=None):
        return self.to_dict().get(key, default)
