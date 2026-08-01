"""路由結果結構（F09 4.6：RoutingResult）。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RoutingResult:
    """路由結果（F09 4.6）。"""

    selected_skills: list[str] = field(default_factory=list)
    executed_skills: list[str] = field(default_factory=list)
    skill_results: dict[str, dict] = field(default_factory=dict)
    recommended_action: str = "ALLOW"
    rewritten_prompt: str | None = None
    added_constraints: list[str] = field(default_factory=list)
    runtime_monitor_level: str = "low"
    blocked: bool = False
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "selected_skills": self.selected_skills,
            "executed_skills": self.executed_skills,
            "skill_results": self.skill_results,
            "recommended_action": self.recommended_action,
            "rewritten_prompt": self.rewritten_prompt,
            "added_constraints": self.added_constraints,
            "runtime_monitor_level": self.runtime_monitor_level,
            "blocked": self.blocked,
            "reasons": self.reasons,
        }
