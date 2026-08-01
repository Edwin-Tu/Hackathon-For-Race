"""資料重建技能（F09 五：data_reconstruction_skill，主要動作 BLOCK）。"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.keyword_skill_base import KeywordBasedSkill


class DataReconstructionSkill(KeywordBasedSkill):
    skill_name = "data_reconstruction_skill"
    attack_categories = ["data_reconstruction"]
    default_action = PolicyAction.BLOCK.value
    refusal_message = "無法透過片段拼接、逐字元列出等方式重建受保護內容。"
