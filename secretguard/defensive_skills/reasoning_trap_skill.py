"""推理陷阱技能（F09 五：reasoning_trap_skill，主要動作為警告文字）。"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.keyword_skill_base import KeywordBasedSkill


class ReasoningTrapSkill(KeywordBasedSkill):
    skill_name = "reasoning_trap_skill"
    attack_categories = ["reasoning_trap"]
    default_action = PolicyAction.WARN.value
    refusal_message = "無法透過假設性情境或思想實驗間接推導出受保護資訊。"
