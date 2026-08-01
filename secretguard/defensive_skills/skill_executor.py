"""技能執行器（F09 三：skill_executor）。

負責實際呼叫單一技能的 detect/defend，並統一例外處理，避免單一技能出錯
拖垮整個路由流程（fail-safe：技能執行失敗時預設為 WARN 並記錄原因）。
"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.base_skill import BaseSkill
from secretguard.defensive_skills.skill_models import DefenseResult, DetectionResult, SkillInput


def execute_skill(
    skill: BaseSkill, skill_input: SkillInput
) -> tuple[DetectionResult, DefenseResult]:
    """執行單一技能，回傳 (DetectionResult, DefenseResult)。"""

    try:
        detection = skill.detect(skill_input)
        defense = skill.defend(skill_input, detection)
        return detection, defense
    except Exception as exc:  # noqa: BLE001 - 技能執行需 fail-safe，不可讓單一技能拖垮路由
        fallback_detection = DetectionResult(
            matched=False,
            confidence=0.0,
            reasons=[f"技能 {getattr(skill, 'skill_name', 'unknown')} 執行時發生例外: {exc}"],
        )
        fallback_defense = DefenseResult(
            action=PolicyAction.WARN.value,
            response_message="偵測系統發生內部錯誤，已採取保守警告動作。",
            evidence={"error": str(exc)},
        )
        return fallback_detection, fallback_defense


def execute_skills(
    skills: list[BaseSkill], skill_input: SkillInput
) -> list[tuple[str, DetectionResult, DefenseResult]]:
    """依序執行多個技能，回傳每個技能的 (skill_name, detection, defense)。"""

    results = []
    for skill in skills:
        detection, defense = execute_skill(skill, skill_input)
        results.append((getattr(skill, "skill_name", skill.__class__.__name__), detection, defense))
    return results
