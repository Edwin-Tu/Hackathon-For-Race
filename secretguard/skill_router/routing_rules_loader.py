"""載入 routing_rules.json（F09 4.7）。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

_ROUTING_RULES_PATH = Path(__file__).parent / "routing_rules.json"


@dataclass
class RoutingRule:
    """單一攻擊類別的路由規則（F09 4.7）。"""

    category: str
    primary_skill: str
    secondary_skills: list[str] = field(default_factory=list)
    priority: int = 100
    min_policy_action: str = "WARN"


@lru_cache(maxsize=1)
def load_routing_rules(path: Path | None = None) -> dict[str, RoutingRule]:
    """載入路由規則，回傳 category -> RoutingRule 對應表。"""

    target = path or _ROUTING_RULES_PATH
    with target.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    rules: dict[str, RoutingRule] = {}
    for category, data in raw.items():
        rules[category] = RoutingRule(
            category=category,
            primary_skill=data.get("primary_skill", ""),
            secondary_skills=list(data.get("secondary_skills", [])),
            priority=int(data.get("priority", 100)),
            min_policy_action=data.get("min_policy_action", "WARN"),
        )
    return rules


def get_routing_rule(category: str) -> RoutingRule | None:
    return load_routing_rules().get(category)
