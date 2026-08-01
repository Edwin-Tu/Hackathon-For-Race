"""人格覆寫技能（F09 五：persona_override_skill，主要動作 BLOCK）。"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.keyword_skill_base import KeywordBasedSkill


class PersonaOverrideSkill(KeywordBasedSkill):
    skill_name = "persona_override_skill"
    attack_categories = ["persona_override"]
    default_action = PolicyAction.BLOCK.value
    refusal_message = "無法永久或深層改變系統設定的身份人格。"
