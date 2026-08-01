"""部分揭露技能（F09 五：partial_disclosure_skill，主要動作 BLOCK）。"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.keyword_skill_base import KeywordBasedSkill


class PartialDisclosureSkill(KeywordBasedSkill):
    skill_name = "partial_disclosure_skill"
    attack_categories = ["partial_disclosure"]
    default_action = PolicyAction.BLOCK.value
    refusal_message = "無法揭露機密的任何部分片段，包括前後幾位字元。"
