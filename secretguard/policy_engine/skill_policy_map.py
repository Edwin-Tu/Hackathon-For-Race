"""攻擊類別到所需技能的對應（F10 六之 3：政策引擎決定所需技能）。

直接複用 F09 skill_router 的路由規則作為單一事實來源，避免兩處各自維護
類別->技能對應而產生不一致（呼應 F09 八之 3：優先序與路由規則一致性）。
"""

from __future__ import annotations

from secretguard.skill_router.routing_rules_loader import get_routing_rule


def required_skills_for_category(category: str | None) -> list[str]:
    """取得攻擊類別對應的必要技能清單（primary + secondary）。"""

    if not category:
        return []
    rule = get_routing_rule(category)
    if rule is None:
        return []
    skills = []
    if rule.primary_skill:
        skills.append(rule.primary_skill)
    skills.extend(rule.secondary_skills)
    return skills
