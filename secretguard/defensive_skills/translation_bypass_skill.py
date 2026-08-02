"""翻譯繞過技能（F09 五：translation_bypass_skill，主要動作 RESTRICT）。"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.keyword_skill_base import KeywordBasedSkill


class TranslationBypassSkill(KeywordBasedSkill):
    skill_name = "translation_bypass_skill"
    attack_categories = ["translation_bypass"]
    default_action = PolicyAction.RESTRICT.value
    refusal_message = "無法透過翻譯成其他語言的方式提供受保護資訊。"
