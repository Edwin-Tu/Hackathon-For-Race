"""存取紀錄技能（F09 五：log_access_skill，主要動作 BLOCK）。"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.keyword_skill_base import KeywordBasedSkill


class LogAccessSkill(KeywordBasedSkill):
    skill_name = "log_access_skill"
    attack_categories = ["log_access"]
    default_action = PolicyAction.BLOCK.value
    refusal_message = "無法提供系統日誌或審計紀錄的存取權限。"
