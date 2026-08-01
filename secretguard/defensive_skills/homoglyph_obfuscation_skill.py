"""相似字形混淆技能（F09 五：homoglyph_obfuscation_skill，主要動作 BLOCK）。"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.keyword_skill_base import KeywordBasedSkill


class HomoglyphObfuscationSkill(KeywordBasedSkill):
    skill_name = "homoglyph_obfuscation_skill"
    attack_categories = ["homoglyph_obfuscation"]
    default_action = PolicyAction.BLOCK.value
    refusal_message = "偵測到以相似字形字元混淆敏感詞彙的請求，已阻擋處理。"
