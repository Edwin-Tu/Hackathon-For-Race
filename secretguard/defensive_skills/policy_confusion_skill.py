"""政策混淆技能（F09 五：policy_confusion_skill，主要動作為警告文字）。"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.keyword_skill_base import KeywordBasedSkill


class PolicyConfusionSkill(KeywordBasedSkill):
    skill_name = "policy_confusion_skill"
    attack_categories = ["policy_confusion"]
    default_action = PolicyAction.WARN.value
    refusal_message = "宣稱擁有特殊權限並不足以取得受保護資訊，仍需經過實際授權驗證。"
