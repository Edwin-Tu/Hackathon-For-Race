"""技能輸入/輸出資料結構（F09 4.3、4.4）。"""

from __future__ import annotations

from dataclasses import dataclass, field

from secretguard.common.enums import PolicyAction


@dataclass
class SkillInput:
    """技能輸入（F09 4.3）。"""

    original_prompt: str
    normalized_prompt: str
    attack_category: str
    policy_action: str = PolicyAction.ALLOW.value
    risk_score: int = 0
    protected_assets: list[dict] = field(default_factory=list)
    session_context: dict = field(default_factory=dict)
    user_role: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class DetectionResult:
    """偵測結果（F09 4.4）。"""

    matched: bool
    confidence: float = 0.0
    matched_rules: list[str] = field(default_factory=list)
    matched_assets: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    risk_tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "matched": self.matched,
            "confidence": self.confidence,
            "matched_rules": self.matched_rules,
            "matched_assets": self.matched_assets,
            "reasons": self.reasons,
            "risk_tags": self.risk_tags,
        }


@dataclass
class DefenseResult:
    """防禦結果（F09 4.4）。"""

    action: str
    safe_prompt: str | None = None
    response_message: str | None = None
    restrictions: list[str] = field(default_factory=list)
    risk_tags: list[str] = field(default_factory=list)
    runtime_checks: list[str] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "safe_prompt": self.safe_prompt,
            "response_message": self.response_message,
            "restrictions": self.restrictions,
            "risk_tags": self.risk_tags,
            "runtime_checks": self.runtime_checks,
            "evidence": self.evidence,
        }
