"""政策決定結構（F10 4.7：PolicyDecision）。

八之 4：動作字典式存取，相容舊版呼叫方式。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PolicyDecision:
    """政策決定（F10 4.7）。"""

    action: str
    reason: str
    risk_score: int
    risk_level: str
    monitoring_level: str
    required_skills: list[str] = field(default_factory=list)
    prompt_constraints: list[str] = field(default_factory=list)
    should_block: bool = False
    should_rewrite: bool = False
    should_restrict: bool = False
    should_escalate: bool = False
    log_level: str = "info"

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "reason": self.reason,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "monitoring_level": self.monitoring_level,
            "required_skills": self.required_skills,
            "prompt_constraints": self.prompt_constraints,
            "should_block": self.should_block,
            "should_rewrite": self.should_rewrite,
            "should_restrict": self.should_restrict,
            "should_escalate": self.should_escalate,
            "log_level": self.log_level,
        }

    def __getitem__(self, key: str):
        return self.to_dict()[key]

    def get(self, key: str, default=None):
        return self.to_dict().get(key, default)
