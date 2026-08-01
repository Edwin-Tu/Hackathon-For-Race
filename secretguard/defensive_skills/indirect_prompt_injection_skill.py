"""間接注入技能（F09 五：indirect_prompt_injection_skill，主要動作 BLOCK）。"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.keyword_skill_base import KeywordBasedSkill


class IndirectPromptInjectionSkill(KeywordBasedSkill):
    skill_name = "indirect_prompt_injection_skill"
    attack_categories = ["indirect_prompt_injection"]
    default_action = PolicyAction.BLOCK.value
    refusal_message = "無法執行來自外部文件或使用者提供內容中夾帶的指令。"
