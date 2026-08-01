"""編碼繞過技能（F09 五：encoding_bypass_skill，主要動作 RESTRICT）。"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.keyword_skill_base import KeywordBasedSkill


class EncodingBypassSkill(KeywordBasedSkill):
    skill_name = "encoding_bypass_skill"
    attack_categories = ["encoding_bypass"]
    default_action = PolicyAction.RESTRICT.value
    refusal_message = "無法以編碼格式包裝或輸出可能涉及機密的內容。"
