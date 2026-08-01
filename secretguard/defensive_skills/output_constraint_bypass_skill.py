"""繞過輸出限制技能（F09 五：output_constraint_bypass_skill，主要動作 BLOCK）。"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.keyword_skill_base import KeywordBasedSkill


class OutputConstraintBypassSkill(KeywordBasedSkill):
    skill_name = "output_constraint_bypass_skill"
    attack_categories = ["output_constraint_bypass"]
    default_action = PolicyAction.BLOCK.value
    refusal_message = "無法提供不受任何內容政策限制的回答。"
