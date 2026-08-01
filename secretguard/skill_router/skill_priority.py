"""技能優先序管理（F09 4.8：SkillRegistry 內部之技能優先序對應）。

優先序數字越小代表越優先執行（與 routing_rules.json 的 priority 語意一致）。
本模組把「路由規則的優先序」轉為「技能名稱 -> 優先序」的扁平對應表，
供 SkillRegistry 查詢與排序使用，確保 F09 八之 3：技能優先序與路由規則一致。
"""

from __future__ import annotations

from secretguard.skill_router.routing_rules_loader import load_routing_rules

DEFAULT_PRIORITY = 100


def build_priority_map() -> dict[str, int]:
    """依 routing_rules.json 建立技能名稱到優先序的對應表。

    若同一技能出現在多個類別的 primary/secondary 中，取數字最小（最優先）者。
    """

    priority_map: dict[str, int] = {}
    for rule in load_routing_rules().values():
        if rule.primary_skill:
            _update_min(priority_map, rule.primary_skill, rule.priority)
        for secondary in rule.secondary_skills:
            # 次要技能優先序略低於主要技能（+5），避免搶在主要技能之前執行
            _update_min(priority_map, secondary, rule.priority + 5)
    return priority_map


def _update_min(mapping: dict[str, int], key: str, value: int) -> None:
    if key not in mapping or value < mapping[key]:
        mapping[key] = value


def get_priority(skill_name: str, priority_map: dict[str, int] | None = None) -> int:
    mapping = priority_map if priority_map is not None else build_priority_map()
    return mapping.get(skill_name, DEFAULT_PRIORITY)
