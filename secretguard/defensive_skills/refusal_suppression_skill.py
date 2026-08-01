"""壓制拒絕技能（F09 五：refusal_suppression_skill，主要動作 BLOCK）。"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.keyword_skill_base import KeywordBasedSkill


class RefusalSuppressionSkill(KeywordBasedSkill):
    skill_name = "refusal_suppression_skill"
    attack_categories = ["refusal_suppression"]
    default_action = PolicyAction.BLOCK.value
    refusal_message = "系統保留在必要時拒絕回答的權利，不受使用者指示壓制。"
