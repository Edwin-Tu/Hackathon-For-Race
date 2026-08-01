"""路由情境結構（F09 4.6：RoutingContext）。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RoutingContext:
    """路由情境（F09 4.6）。"""

    prompt: str
    attack_categories: list[str] = field(default_factory=list)
    policy_action: str = "ALLOW"
    risk_score: int = 0
    protected_assets: list[dict] = field(default_factory=list)
    matched_rules: list[str] = field(default_factory=list)
    session_context: dict = field(default_factory=dict)
    user_role: str | None = None
    normalized_prompt: str = ""
