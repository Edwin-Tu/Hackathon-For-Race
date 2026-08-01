"""格式夾帶技能（F09 五：format_smuggling_skill，主要動作為警告文字）。"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.keyword_skill_base import KeywordBasedSkill


class FormatSmugglingSkill(KeywordBasedSkill):
    skill_name = "format_smuggling_skill"
    attack_categories = ["format_smuggling"]
    default_action = PolicyAction.WARN.value
    refusal_message = "已忽略文字中以特殊格式（如註解、標籤）夾帶的隱藏指令。"
