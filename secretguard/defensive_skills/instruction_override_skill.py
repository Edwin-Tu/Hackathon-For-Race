"""覆寫指令技能（F09 五：instruction_override_skill，主要動作 BLOCK）。"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.keyword_skill_base import KeywordBasedSkill


class InstructionOverrideSkill(KeywordBasedSkill):
    skill_name = "instruction_override_skill"
    attack_categories = ["instruction_override"]
    default_action = PolicyAction.BLOCK.value
    refusal_message = "系統指令不可被使用者請求覆寫或忽略。"
