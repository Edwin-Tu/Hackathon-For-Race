"""Risk scoring that keeps attack risk separate from authorization/access risk."""

from __future__ import annotations

from secretguard.risk_scoring.risk_score_result import RiskScoreResult
from secretguard.risk_scoring.score_calculator import (
    action_for_risk_level,
    clamp_score,
    risk_level_for_score,
    score_asset_risk,
    score_attack_category,
    score_match_type,
)
from secretguard.risk_scoring.session_risk_tracker import assess_signals

_OBFUSCATION_FLAGS = {
    "unicode_confusable_detected",
    "zero_width_character_removed",
    "spacing_obfuscation_detected",
    "symbol_obfuscation_detected",
    "base64_candidate_detected",
    "hex_candidate_detected",
    "url_encoding_candidate_detected",
    "cross_language_alias_detected",
    "reconstruction_pattern_detected",
}
_HIGH_RISK_OPERATIONS = {"DISCLOSE", "EXTRACT", "RECONSTRUCT", "TRANSFORM"}


class RiskScoringEngine:
    def score(
        self,
        attack_category: str | None = None,
        confidence: float | None = None,
        matched_assets: list[dict] | None = None,
        triggered_rules: list[str] | None = None,
        authorization_status: str = "unauthorized",
        session_signals: list[str] | None = None,
        intent_asset_reference_type: str | None = None,
        intent_operation: str | None = None,
        intent_scope: str | None = None,
        intent_disclosure_mode: str | None = None,
        input_guard_flags: list[str] | None = None,
        cross_scope_request: bool = False,
    ) -> RiskScoreResult:
        matched_assets = matched_assets or []
        triggered_rules = triggered_rules or []
        session_signals = session_signals or []
        input_guard_flags = input_guard_flags or []
        factors: list[str] = []

        # Attack risk: authorization never subtracts from this score.
        attack_component = min(70, score_attack_category(attack_category))
        intent_component = 0
        if intent_operation in _HIGH_RISK_OPERATIONS:
            intent_component += 20
        if intent_scope in {"CURRENT_SYSTEM", "PROTECTED_REGISTRY"}:
            intent_component += 8
        if intent_disclosure_mode in {"FULL_VALUE", "ENCODED_VALUE", "RECONSTRUCTED_VALUE"}:
            intent_component += 7
        intent_component = min(30, intent_component)

        session_assessment = assess_signals(session_signals)
        session_component = min(25, session_assessment.total_score)
        obfuscation_count = len(set(input_guard_flags) & _OBFUSCATION_FLAGS)
        obfuscation_component = min(15, obfuscation_count * 5)
        attack_score = clamp_score(
            attack_component + intent_component + session_component + obfuscation_component
        )

        if attack_component:
            factors.append(f"attack_category:{attack_category}:{attack_component}")
        if intent_component:
            factors.append(f"attack_intent:{intent_component}")
        if session_component:
            factors.append(f"session:{session_component}")
        if obfuscation_component:
            factors.append(f"obfuscation:{obfuscation_component}")

        # Access risk: evaluated only when a protected/current-system scope is requested.
        access_targeted = cross_scope_request or intent_operation in _HIGH_RISK_OPERATIONS
        asset_component = (
            max((score_asset_risk(a.get("risk_level", "low")) for a in matched_assets), default=0)
            if access_targeted else 0
        )
        match_component = (
            min(30, max((score_match_type(a.get("match_type", "")) for a in matched_assets), default=0))
            if access_targeted else 0
        )
        authorization_component = 0
        if access_targeted:
            if authorization_status in {"unauthorized", "unknown"}:
                authorization_component = 30
            elif authorization_status == "role_claim_only":
                authorization_component = 40
        if cross_scope_request:
            authorization_component = max(authorization_component, 50)

        access_score = clamp_score(asset_component + match_component + authorization_component)
        if asset_component:
            factors.append(f"asset:{asset_component}")
        if match_component:
            factors.append(f"match_type:{match_component}")
        if authorization_component:
            factors.append(f"authorization:{authorization_component}")

        overall = max(attack_score, access_score)
        level = risk_level_for_score(overall)
        action = action_for_risk_level(level)
        requires_authorization = access_targeted and authorization_status not in {"owner", "authorized"}

        safe_assets = [
            {
                "asset_id": item.get("asset_id"),
                "risk_level": item.get("risk_level", "low"),
                "match_type": item.get("match_type", ""),
            }
            for item in matched_assets
        ]
        return RiskScoreResult(
            risk_score=overall,
            risk_level=level,
            recommended_action=action,
            attack_risk_score=attack_score,
            access_risk_score=access_score,
            risk_breakdown={
                "attack": attack_component,
                "asset": asset_component,
                "intent": intent_component,
                "session": session_component,
                "obfuscation": obfuscation_component,
                "access": authorization_component + match_component,
            },
            risk_factors=factors,
            matched_assets=safe_assets,
            triggered_rules=list(triggered_rules),
            attack_category=attack_category,
            confidence=confidence,
            requires_authorization=requires_authorization,
            enable_strict_runtime_monitor=overall >= 60,
        )
