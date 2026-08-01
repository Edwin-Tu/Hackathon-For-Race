"""提取系統提示詞技能（F09 五：system_prompt_extraction_skill，主要動作 BLOCK）。"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.keyword_skill_base import KeywordBasedSkill


class SystemPromptExtractionSkill(KeywordBasedSkill):
    skill_name = "system_prompt_extraction_skill"
    attack_categories = ["system_prompt_extraction"]
    default_action = PolicyAction.BLOCK.value
    refusal_message = "系統提示詞屬於內部機密，無法對外提供。"
