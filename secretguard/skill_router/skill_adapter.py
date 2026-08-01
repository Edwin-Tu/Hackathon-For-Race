"""技能介面轉接器（F09 五注意事項）。

技能存在兩代介面：
- 現代介面：skill_name / attack_categories 類別屬性 + detect(skill_input) / defend(skill_input, detection)
- 舊版介面：name 屬性 + detect(text) / defend(text, detection) 這類較簡化的簽名

SkillAdapter 把任意技能物件轉接成統一呼叫方式，讓 skill_router 不需關心
技能實際採用哪一代介面。
"""

from __future__ import annotations

from typing import Any

from secretguard.defensive_skills.skill_models import DefenseResult, DetectionResult, SkillInput


class SkillAdapter:
    """把現代或舊版介面的技能物件統一包裝成 (name, run(skill_input)) 介面。"""

    def __init__(self, skill: Any):
        self._skill = skill
        self.name = self._resolve_name(skill)

    @staticmethod
    def _resolve_name(skill: Any) -> str:
        if hasattr(skill, "skill_name"):
            return skill.skill_name
        if hasattr(skill, "name"):
            name_attr = skill.name
            return name_attr() if callable(name_attr) else name_attr
        return skill.__class__.__name__

    def run(self, skill_input: SkillInput) -> tuple[DetectionResult, DefenseResult]:
        """統一執行入口：偵測現代介面優先，否則嘗試轉接舊版介面。"""

        if hasattr(self._skill, "detect") and hasattr(self._skill, "defend"):
            try:
                detection = self._skill.detect(skill_input)
                defense = self._skill.defend(skill_input, detection)
                if isinstance(detection, DetectionResult) and isinstance(
                    defense, DefenseResult
                ):
                    return detection, defense
            except TypeError:
                # 現代介面呼叫失敗，嘗試以舊版介面（僅傳文字）呼叫
                pass

        return self._run_legacy(skill_input)

    def _run_legacy(self, skill_input: SkillInput) -> tuple[DetectionResult, DefenseResult]:
        """舊版介面轉接：detect(text) -> dict/bool，defend(text, detection) -> dict/str。"""

        text = skill_input.normalized_prompt or skill_input.original_prompt
        raw_detection = self._skill.detect(text)

        matched = bool(raw_detection)
        reasons: list[str] = []
        confidence = 0.5
        if isinstance(raw_detection, dict):
            matched = bool(raw_detection.get("matched", matched))
            confidence = float(raw_detection.get("confidence", confidence))
            reasons = list(raw_detection.get("reasons", []))

        detection = DetectionResult(
            matched=matched,
            confidence=confidence,
            matched_rules=[self.name],
            reasons=reasons or [f"舊版技能 {self.name} 判定為 {'命中' if matched else '未命中'}"],
        )

        raw_defense = self._skill.defend(text, raw_detection)
        action = "WARN"
        response_message = None
        if isinstance(raw_defense, dict):
            action = raw_defense.get("action", action)
            response_message = raw_defense.get("response_message")
        elif isinstance(raw_defense, str):
            response_message = raw_defense

        defense = DefenseResult(action=action, response_message=response_message)
        return detection, defense
