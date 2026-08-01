"""結構化輸出技能（F09 五：structured_output_skill，主要動作附加警告）。"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.keyword_skill_base import KeywordBasedSkill


class StructuredOutputSkill(KeywordBasedSkill):
    skill_name = "structured_output_skill"
    attack_categories = ["structured_output"]
    default_action = PolicyAction.WARN.value
    refusal_message = "回應將以結構化格式輸出，但仍會排除任何受保護資產原始值。"
