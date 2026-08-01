"""技能路由主體（F09 三、六）。

依路由規則選擇技能、依優先序執行、彙整最終建議動作與重寫提示詞。
"""

from __future__ import annotations

from secretguard.common.enums import ACTION_SEVERITY, PolicyAction
from secretguard.defensive_skills.skill_models import SkillInput
from secretguard.skill_router.routing_context import RoutingContext
from secretguard.skill_router.routing_result import RoutingResult
from secretguard.skill_router.routing_rules_loader import get_routing_rule
from secretguard.skill_router.skill_registry import SkillRegistry

# 動作到運行監控等級的對應（呼應 F10 五之監控等級對應，供 F14 使用）。
_ACTION_MONITOR_LEVEL = {
    PolicyAction.ALLOW.value: "low",
    PolicyAction.WARN.value: "medium",
    PolicyAction.REWRITE.value: "medium",
    PolicyAction.RESTRICT.value: "high",
    PolicyAction.AUTHORIZE.value: "high",
    PolicyAction.ESCALATE.value: "critical",
    PolicyAction.BLOCK.value: "critical",
}

_BLOCKING_ACTIONS = {PolicyAction.BLOCK.value, PolicyAction.ESCALATE.value}


class SkillRouter:
    """技能路由：選擇、排序、執行技能並彙整結果。"""

    def __init__(self, registry: SkillRegistry | None = None) -> None:
        self._registry = registry or SkillRegistry()

    def route(self, context: RoutingContext) -> RoutingResult:
        """依路由情境選擇並執行技能，回傳彙整後的路由結果。"""

        selected_skills = self._select_skills(context.attack_categories)
        ordered_skills = self._registry.sort_by_priority(selected_skills)

        skill_input = SkillInput(
            original_prompt=context.prompt,
            normalized_prompt=context.normalized_prompt or context.prompt,
            attack_category=context.attack_categories[0] if context.attack_categories else "benign",
            policy_action=context.policy_action,
            risk_score=context.risk_score,
            protected_assets=context.protected_assets,
            session_context=context.session_context,
            user_role=context.user_role,
        )

        result = RoutingResult(selected_skills=ordered_skills)

        actions: list[str] = []
        constraints: list[str] = []
        rewritten_prompt: str | None = None
        reasons: list[str] = []

        for skill_name in ordered_skills:
            adapter = self._registry.get_skill(skill_name)
            if adapter is None:
                continue
            detection, defense = adapter.run(skill_input)
            result.executed_skills.append(skill_name)
            result.skill_results[skill_name] = {
                "detection": detection.to_dict(),
                "defense": defense.to_dict(),
            }

            if not detection.matched:
                continue

            actions.append(defense.action)
            constraints.extend(defense.restrictions)
            if defense.response_message:
                reasons.append(f"{skill_name}: {defense.response_message}")
            if defense.safe_prompt and rewritten_prompt is None:
                rewritten_prompt = defense.safe_prompt

        # 套用路由規則的最低政策動作門檻（min_policy_action），
        # 確保即使技能判定較寬鬆，也不會低於該類別規定的最低動作。
        for category in context.attack_categories:
            rule = get_routing_rule(category)
            if rule and rule.min_policy_action:
                actions.append(rule.min_policy_action)

        recommended_action = self._max_severity(actions) if actions else PolicyAction.ALLOW.value

        result.recommended_action = recommended_action
        result.rewritten_prompt = rewritten_prompt
        result.added_constraints = sorted(set(constraints))
        result.runtime_monitor_level = _ACTION_MONITOR_LEVEL.get(recommended_action, "low")
        result.blocked = recommended_action in _BLOCKING_ACTIONS
        result.reasons = reasons

        return result

    def _select_skills(self, attack_categories: list[str]) -> list[str]:
        """依攻擊類別挑選 primary + secondary 技能清單（去重）。"""

        selected: list[str] = []
        for category in attack_categories:
            rule = get_routing_rule(category)
            if rule is None:
                continue
            if rule.primary_skill and rule.primary_skill not in selected:
                selected.append(rule.primary_skill)
            for secondary in rule.secondary_skills:
                if secondary not in selected:
                    selected.append(secondary)
        return selected

    @staticmethod
    def _max_severity(actions: list[str]) -> str:
        valid_actions = [a for a in actions if a in ACTION_SEVERITY]
        if not valid_actions:
            return PolicyAction.ALLOW.value
        return max(valid_actions, key=lambda a: ACTION_SEVERITY[a])
