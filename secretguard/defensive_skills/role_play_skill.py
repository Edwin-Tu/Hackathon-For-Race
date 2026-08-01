"""角色扮演繞過技能（F09 五：role_play_skill，主要動作 BLOCK）。"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.keyword_skill_base import KeywordBasedSkill


class RolePlaySkill(KeywordBasedSkill):
    skill_name = "role_play_skill"
    attack_categories = ["role_play"]
    default_action = PolicyAction.BLOCK.value
    refusal_message = "無法配合改變身份設定或扮演無限制角色的請求。"
