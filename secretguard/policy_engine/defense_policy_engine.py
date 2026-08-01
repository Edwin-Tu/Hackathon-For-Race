"""Hard-rule-first policy engine for Input Guard."""

from __future__ import annotations

from secretguard.common.enums import PolicyAction
from secretguard.policy_engine.policy_context import PolicyContext
from secretguard.policy_engine.policy_decision import PolicyDecision
from secretguard.policy_engine.skill_policy_map import required_skills_for_category

_RISK_THRESHOLD_ACTIONS = [
    (0, 19, PolicyAction.ALLOW),
    (20, 39, PolicyAction.WARN),
    (40, 59, PolicyAction.REWRITE),
    (60, 74, PolicyAction.RESTRICT),
    (75, 100, PolicyAction.BLOCK),
]
_MONITORING_LEVEL_MAP = {
    PolicyAction.ALLOW: "low",
    PolicyAction.WARN: "medium",
    PolicyAction.REWRITE: "medium",
    PolicyAction.RESTRICT: "high",
    PolicyAction.AUTHORIZE: "high",
    PolicyAction.ESCALATE: "critical",
    PolicyAction.BLOCK: "critical",
}
_LOG_LEVEL_MAP = {
    PolicyAction.ALLOW: "info",
    PolicyAction.WARN: "warning",
    PolicyAction.REWRITE: "warning",
    PolicyAction.RESTRICT: "warning",
    PolicyAction.AUTHORIZE: "warning",
    PolicyAction.ESCALATE: "error",
    PolicyAction.BLOCK: "error",
}

_ALWAYS_BLOCK = {
    "system_prompt_extraction",
    "indirect_prompt_injection",
    "data_reconstruction",
}
_HIGH_CONFIDENCE_BLOCK = {
    "instruction_override",
    "role_play",
    "persona_override",
    "refusal_suppression",
    "output_constraint_bypass",
}
_RESTRICT_CATEGORIES = {
    "encoding_bypass",
    "translation_bypass",
    "partial_disclosure",
    "format_smuggling",
    "structured_output",
    "log_access",
    "cross_language_injection",
    "homoglyph_obfuscation",
}


def _base_action(score: int) -> PolicyAction:
    for low, high, action in _RISK_THRESHOLD_ACTIONS:
        if low <= score <= high:
            return action
    return PolicyAction.BLOCK if score > 100 else PolicyAction.ALLOW


class DefensePolicyEngine:
    def decide(self, context: PolicyContext) -> PolicyDecision:
        reasons: list[str] = []
        constraints = list(context.input_guard_flags)

        # 1. Explicit benign educational/security-analysis context.
        if (
            context.scope == "GENERAL_CONCEPT"
            and context.operation == "EXPLAIN"
            and not context.is_attack
        ):
            action = PolicyAction.ALLOW
            reasons.append("general_concept_safe_context")
        # 2. Hard blocks independent of identity or authorization.
        elif context.attack_category in _ALWAYS_BLOCK:
            action = PolicyAction.BLOCK
            reasons.append(f"hard_block:{context.attack_category}")
        elif (
            context.attack_category in _HIGH_CONFIDENCE_BLOCK
            and context.classifier_confidence >= 0.65
        ):
            action = PolicyAction.BLOCK
            reasons.append(f"high_confidence_attack:{context.attack_category}")
        # 3. Cross-scope access attempts require authorization or are blocked.
        elif context.attack_category == "authorization_bypass" or context.cross_scope_request:
            action = PolicyAction.AUTHORIZE if not context.is_authorized else PolicyAction.BLOCK
            reasons.append("cross_scope_access_request")
        # 4. Category-specific restrictions are evaluated before generic authorization.
        elif context.attack_category == "multi_turn_probe" or context.session_risk_score >= 60:
            action = PolicyAction.ESCALATE
            reasons.append("multi_turn_or_session_escalation")
        elif context.attack_category in _RESTRICT_CATEGORIES and context.is_attack:
            action = PolicyAction.RESTRICT
            reasons.append(f"restricted_attack_category:{context.attack_category}")
        elif context.attack_category == "direct_request" and context.is_attack:
            action = PolicyAction.AUTHORIZE if not context.is_authorized else PolicyAction.RESTRICT
            reasons.append("direct_sensitive_request")
        # 5. Direct protected-data extraction is an access-control decision.
        elif context.operation in {"DISCLOSE", "EXTRACT", "RECONSTRUCT", "TRANSFORM"}:
            if context.attack_category in {"system_prompt_extraction", "data_reconstruction"}:
                action = PolicyAction.BLOCK
                reasons.append("protected_attack_extraction")
            elif not context.is_authorized or context.access_risk_score >= 60:
                action = PolicyAction.AUTHORIZE
                reasons.append("authorization_required")
            else:
                action = PolicyAction.RESTRICT
                reasons.append("authorized_but_sensitive_operation")
        else:
            action = _base_action(max(context.attack_risk_score, context.access_risk_score, context.risk_score))
            reasons.append(f"score_threshold:{action.value}")

        # An authenticated owner never receives a lower attack action merely due to identity.
        # Authorization affects data access only; it does not downgrade prompt injection.
        if context.is_attack and action == PolicyAction.ALLOW:
            action = PolicyAction.WARN
            reasons.append("attack_cannot_be_silently_allowed")

        return PolicyDecision(
            action=action.value,
            reason="; ".join(reasons),
            risk_score=context.risk_score,
            risk_level=context.risk_level,
            monitoring_level=_MONITORING_LEVEL_MAP[action],
            required_skills=required_skills_for_category(context.attack_category),
            prompt_constraints=constraints,
            should_block=action == PolicyAction.BLOCK,
            should_rewrite=action == PolicyAction.REWRITE,
            should_restrict=action in {PolicyAction.RESTRICT, PolicyAction.AUTHORIZE},
            should_escalate=action == PolicyAction.ESCALATE,
            log_level=_LOG_LEVEL_MAP[action],
        )
