"""跨語言注入技能（F09 五：cross_language_injection_skill，主要動作 BLOCK）。"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.keyword_skill_base import KeywordBasedSkill


class CrossLanguageInjectionSkill(KeywordBasedSkill):
    skill_name = "cross_language_injection_skill"
    attack_categories = ["cross_language_injection"]
    default_action = PolicyAction.BLOCK.value
    refusal_message = "無法配合以其他語言重述的指令覆寫或機密請求。"
