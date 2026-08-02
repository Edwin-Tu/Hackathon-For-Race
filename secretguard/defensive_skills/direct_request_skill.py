"""直接索取機密技能（F09 五：direct_request_skill，主要動作 BLOCK）。"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.keyword_skill_base import KeywordBasedSkill


class DirectRequestSkill(KeywordBasedSkill):
    skill_name = "direct_request_skill"
    attack_categories = ["direct_request"]
    default_action = PolicyAction.BLOCK.value
    refusal_message = "無法直接提供密碼、金鑰等機密資訊，請透過授權管道申請存取。"
