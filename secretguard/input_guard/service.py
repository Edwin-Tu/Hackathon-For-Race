"""Unified deterministic Input Guard orchestration service."""

from __future__ import annotations

import re
from collections import defaultdict
from threading import RLock
from typing import Any

from secretguard.asset_registry.protected_asset_registry import ProtectedAssetRegistry
from secretguard.attack_classifier.classifier import AttackClassifier
from secretguard.common.enums import PolicyAction
from secretguard.input_guard.intent import infer_intent
from secretguard.input_guard.models import InputGuardDecision, InputGuardRequest, RiskBreakdown
from secretguard.input_guard.prevalidator import InputPreValidator, InputValidationError
from secretguard.input_normalization.input_normalizer import normalize
from secretguard.input_normalization.normalization_result import SuspicionFlag
from secretguard.policy_engine.defense_policy_engine import DefensePolicyEngine
from secretguard.policy_engine.policy_context import PolicyContext
from secretguard.risk_scoring.risk_scoring_engine import RiskScoringEngine
from secretguard.risk_scoring.session_risk_tracker import assess_signals

_ROLE_CLAIM = re.compile(
    r"(?:我是|我為|身為)\s*(?:管理員|系統管理員|開發者|owner)|"
    r"(?:i am|i'm|as)\s+(?:the\s+)?(?:admin|administrator|owner|developer)",
    re.IGNORECASE,
)
_RECONSTRUCTION_TEXT = re.compile(
    r"(?:上一輪|前一輪|片段|前半段|後半段|拼接|合併|重建|previous turn|previous fragment|combine|reconstruct)",
    re.IGNORECASE,
)


class InputGuardService:
    """Single public entry point for validation, normalization, detection and policy."""

    def __init__(
        self,
        *,
        prevalidator: InputPreValidator | None = None,
        classifier: AttackClassifier | None = None,
        registry: ProtectedAssetRegistry | None = None,
        risk_engine: RiskScoringEngine | None = None,
        policy_engine: DefensePolicyEngine | None = None,
    ) -> None:
        self.prevalidator = prevalidator or InputPreValidator()
        self.classifier = classifier or AttackClassifier()
        self.registry = registry or ProtectedAssetRegistry()
        self.risk_engine = risk_engine or RiskScoringEngine()
        self.policy_engine = policy_engine or DefensePolicyEngine()
        self._session_signals: dict[str, list[str]] = defaultdict(list)
        self._lock = RLock()

    def reset_session(self, session_id: str) -> None:
        with self._lock:
            self._session_signals.pop(session_id, None)

    def inspect(self, request: InputGuardRequest) -> InputGuardDecision:
        try:
            text = self.prevalidator.validate(request.text)
        except InputValidationError as exc:
            return self._validation_block(request, exc)

        normalization = normalize(text)
        if _ROLE_CLAIM.search(text):
            normalization.add_flag(SuspicionFlag.ROLE_CLAIM_DETECTED)

        prior_context = str(request.metadata.get("prior_context", "") or "")
        with self._lock:
            accumulated_signals = list(self._session_signals.get(request.session_id, []))
        session_signals = list(dict.fromkeys(accumulated_signals + request.session_signals))
        if prior_context and _RECONSTRUCTION_TEXT.search(text + " " + prior_context):
            session_signals.append("repeated_partial_request")
            session_context: dict[str, Any] = {"cross_turn_reconstruction": True}
        else:
            session_context = {}
        for signal in session_signals:
            session_context[signal] = True

        asset_matches = self._match_assets(normalization.detection_views())
        classification = self.classifier.classify_normalization(
            normalization,
            session_context=session_context,
        )
        strong_asset_match = any(
            match.match_type in {
                "exact_match", "case_insensitive_match", "partial_match",
                "encoding_match", "reconstruction_match"
            }
            for match in asset_matches
        )
        intent = infer_intent(text, has_asset_match=strong_asset_match)
        if not classification.is_attack and (classification.is_suspicious or intent.educational_context):
            # The classifier recognized a quoted/security-analysis boundary. Do not let
            # quoted attack text create an access-control request downstream.
            from secretguard.input_guard.intent import IntentResult
            intent = IntentResult(
                operation="EXPLAIN",
                scope="GENERAL_CONCEPT",
                disclosure_mode="NONE",
                asset_reference_type="no_asset_reference",
                educational_context=True,
                execution_intent=False,
                cross_scope_request=False,
            )

        # A prompt-only role claim is never trusted as server-side authorization.
        auth_status = request.authorization_status
        if SuspicionFlag.ROLE_CLAIM_DETECTED in normalization.suspicion_flags and auth_status not in {
            "owner",
            "authorized",
        }:
            auth_status = "role_claim_only"

        safe_matches = [match.to_dict() for match in asset_matches]
        risk = self.risk_engine.score(
            attack_category=classification.primary_category,
            confidence=classification.confidence,
            matched_assets=safe_matches,
            triggered_rules=[rule.rule_id for rule in classification.matched_rules],
            authorization_status=auth_status,
            session_signals=session_signals,
            intent_asset_reference_type=intent.asset_reference_type,
            intent_operation=intent.operation,
            intent_scope=intent.scope,
            intent_disclosure_mode=intent.disclosure_mode,
            input_guard_flags=normalization.suspicion_flags,
            cross_scope_request=intent.cross_scope_request,
        )
        session_assessment = assess_signals(session_signals)
        is_authorized = auth_status in {"owner", "authorized"}
        policy = self.policy_engine.decide(
            PolicyContext(
                normalized_prompt=normalization.normalized_text,
                attack_category=classification.primary_category,
                risk_score=risk.risk_score,
                risk_level=risk.risk_level,
                attack_risk_score=risk.attack_risk_score,
                access_risk_score=risk.access_risk_score,
                matched_assets=safe_matches,
                user_role=request.user_role,
                is_authorized=is_authorized,
                authorization_status=auth_status,
                session_risk_score=session_assessment.total_score,
                input_guard_flags=normalization.suspicion_flags,
                classifier_confidence=classification.confidence,
                history_flags=session_signals,
                operation=intent.operation,
                scope=intent.scope,
                disclosure_mode=intent.disclosure_mode,
                asset_reference_type=intent.asset_reference_type,
                is_attack=classification.is_attack,
                is_suspicious=classification.is_suspicious,
                cross_scope_request=intent.cross_scope_request,
            )
        )
        action = PolicyAction(policy.action)
        allowed = action in {PolicyAction.ALLOW, PolicyAction.WARN}
        safe_response = self._safe_response(action)
        safe_normalized_text = self._redact_protected_values(
            normalization.normalized_text,
            asset_matches,
        )

        self._update_session(request.session_id, classification.primary_category, action)
        return InputGuardDecision(
            request_id=request.request_id,
            session_id=request.session_id,
            allowed=allowed,
            action=action,
            normalized_text=safe_normalized_text,
            sanitized_text=safe_normalized_text if allowed else None,
            attack_risk_score=risk.attack_risk_score,
            access_risk_score=risk.access_risk_score,
            overall_risk_score=risk.risk_score,
            overall_risk_level=risk.risk_level,
            risk_breakdown=RiskBreakdown(**risk.risk_breakdown),
            primary_category=classification.primary_category,
            attack_categories=classification.matched_categories,
            is_attack=classification.is_attack,
            is_suspicious=classification.is_suspicious,
            classifier_confidence=classification.confidence,
            matched_rules=[rule.rule_id for rule in classification.matched_rules],
            suspicion_flags=list(normalization.suspicion_flags),
            matched_asset_ids=sorted({match.asset_id for match in asset_matches}),
            requires_authorization=action == PolicyAction.AUTHORIZE or risk.requires_authorization,
            strict_runtime_monitoring=risk.enable_strict_runtime_monitor,
            reason_codes=[part.strip() for part in policy.reason.split(";") if part.strip()],
            safe_response=safe_response,
            metadata={
                "conversation_turn": request.conversation_turn,
                "normalization_transformations": [t.to_dict() for t in normalization.transformations],
                "decoded_candidate_count": len(normalization.decoded_candidates),
                "asset_match_count": len(asset_matches),
                "session_signal_count": len(session_signals),
            },
        )

    @staticmethod
    def _redact_protected_values(text: str, matches) -> str:
        redacted = text
        sensitive_match_types = {
            "exact_match", "case_insensitive_match", "partial_match",
            "encoding_match", "reconstruction_match",
        }
        fragments = sorted(
            {
                match.matched_text
                for match in matches
                if match.match_type in sensitive_match_types and match.matched_text
            },
            key=len,
            reverse=True,
        )
        for fragment in fragments:
            redacted = redacted.replace(fragment, "[PROTECTED_ASSET]")
        return redacted

    def _match_assets(self, views: list[tuple[str, str]]):
        matches = []
        seen: set[tuple[str, str]] = set()
        for _view_name, value in views:
            for match in self.registry.match_text(value):
                key = (match.asset_id, match.match_type)
                if key not in seen:
                    seen.add(key)
                    matches.append(match)
        return matches

    def _update_session(self, session_id: str, category: str, action: PolicyAction) -> None:
        new_signals: list[str] = []
        if action in {PolicyAction.BLOCK, PolicyAction.ESCALATE}:
            new_signals.append("previous_blocked_attempt")
        if category in {"partial_disclosure", "multi_turn_probe", "data_reconstruction"}:
            new_signals.append("repeated_partial_request")
        if category == "encoding_bypass" and action in {PolicyAction.BLOCK, PolicyAction.RESTRICT}:
            new_signals.append("encoding_after_refusal")
        if not new_signals:
            return
        with self._lock:
            existing = self._session_signals[session_id]
            for signal in new_signals:
                if signal not in existing:
                    existing.append(signal)

    @staticmethod
    def _safe_response(action: PolicyAction) -> str | None:
        if action == PolicyAction.AUTHORIZE:
            return "此操作需要額外授權，請確認使用者身分與存取範圍。"
        if action == PolicyAction.ESCALATE:
            return "此請求需要進一步安全審查，暫時無法自動處理。"
        if action in {PolicyAction.BLOCK, PolicyAction.RESTRICT, PolicyAction.REWRITE}:
            return "此請求涉及受限制的資訊或操作，無法直接處理。"
        return None

    @staticmethod
    def _validation_block(request: InputGuardRequest, exc: InputValidationError) -> InputGuardDecision:
        return InputGuardDecision(
            request_id=request.request_id,
            session_id=request.session_id,
            allowed=False,
            action=PolicyAction.BLOCK,
            normalized_text="",
            sanitized_text=None,
            attack_risk_score=100,
            access_risk_score=0,
            overall_risk_score=100,
            overall_risk_level="critical",
            risk_breakdown=RiskBreakdown(attack=100),
            primary_category="input_validation",
            attack_categories=["input_validation"],
            is_attack=False,
            is_suspicious=True,
            classifier_confidence=1.0,
            matched_rules=[],
            suspicion_flags=[exc.code],
            matched_asset_ids=[],
            requires_authorization=False,
            strict_runtime_monitoring=True,
            reason_codes=[exc.code],
            safe_response="輸入格式或長度不符合安全限制。",
            metadata={},
        )
