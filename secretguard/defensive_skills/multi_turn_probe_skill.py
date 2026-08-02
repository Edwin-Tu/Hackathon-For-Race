"""多輪探測技能（F09 五：multi_turn_probe_skill，主要動作 ESCALATE）。

會話感知：需累積會話歷史判斷（F09 八之 2），因此偵測邏輯額外檢查
session_context 中的訊號（例如 previous_blocked_attempt、repeated_partial_request）。
"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.keyword_skill_base import KeywordBasedSkill
from secretguard.defensive_skills.skill_models import DetectionResult, SkillInput


class MultiTurnProbeSkill(KeywordBasedSkill):
    skill_name = "multi_turn_probe_skill"
    attack_categories = ["multi_turn_probe"]
    default_action = PolicyAction.ESCALATE.value
    refusal_message = "偵測到疑似多輪拼湊機密的探測行為，已升級監控等級。"

    def detect(self, skill_input: SkillInput) -> DetectionResult:
        detection = super().detect(skill_input)

        session_signals = []
        if skill_input.session_context.get("previous_blocked_attempt"):
            session_signals.append("previous_blocked_attempt")
        if skill_input.session_context.get("repeated_partial_request"):
            session_signals.append("repeated_partial_request")
        if skill_input.session_context.get("session_marked_suspicious"):
            session_signals.append("session_marked_suspicious")

        if session_signals:
            detection.matched = True
            detection.confidence = max(detection.confidence, 0.75)
            detection.reasons.append(f"會話歷史訊號: {', '.join(session_signals)}")
            if "multi_turn_probe" not in detection.risk_tags:
                detection.risk_tags.append("multi_turn_probe")

        return detection
