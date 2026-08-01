"""Adapter that connects SecretGuard Input Guard to the Agent runtime.

The SecretGuard package owns deterministic normalization, attack classification,
risk scoring, protected-asset matching, and policy evaluation. This adapter owns
only the integration boundary:

- authorization is derived from trusted ``AuthContext``;
- raw user role claims are never treated as authorization;
- failures are fail-closed by default;
- only safe, minimized evidence is exposed to the API response.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.models import InputGuardEvidence
from app.tools import AuthContext, Role
from secretguard.input_guard import InputGuardRequest, InputGuardService

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AgentInputGuardOutcome:
    """Runtime-safe result returned to ``AgentService``."""

    allowed: bool
    sanitized_text: str | None
    safe_response: str | None
    evidence: InputGuardEvidence


class AgentInputGuard:
    """Fail-closed Input Guard facade for Agent chat requests."""

    def __init__(
        self,
        *,
        service: InputGuardService | None = None,
        enabled: bool = True,
        fail_closed: bool = True,
    ) -> None:
        self._service = service or InputGuardService()
        self._enabled = enabled
        self._fail_closed = fail_closed

    @staticmethod
    def _authorization_status(auth_context: AuthContext) -> str:
        """Map trusted backend identity to SecretGuard authorization status."""
        if auth_context.role == Role.RESIDENT:
            if (
                auth_context.active_persona_id
                and auth_context.active_persona_id in auth_context.authorized_persona_ids
            ):
                return "owner"
            return "unauthorized"

        if auth_context.role in {Role.CAREGIVER, Role.FAMILY}:
            return "authorized" if auth_context.authorized_persona_ids else "unauthorized"

        if auth_context.role in {Role.ADMIN, Role.SYSTEM}:
            return "authorized"

        return "unauthorized"

    def inspect(
        self,
        *,
        text: str,
        auth_context: AuthContext,
        conversation_turn: int = 1,
        prior_context: str = "",
    ) -> AgentInputGuardOutcome:
        """Inspect one user message before intent routing or Bedrock invocation."""
        if not self._enabled:
            evidence = InputGuardEvidence(
                enabled=False,
                allowed=True,
                action="ALLOW",
                overall_risk_level="disabled",
                overall_risk_score=0,
                attack_risk_score=0,
                access_risk_score=0,
                primary_category="disabled",
                is_attack=False,
                is_suspicious=False,
                strict_runtime_monitoring=False,
                reason_codes=[],
            )
            return AgentInputGuardOutcome(
                allowed=True,
                sanitized_text=text,
                safe_response=None,
                evidence=evidence,
            )

        try:
            decision = self._service.inspect(
                InputGuardRequest(
                    request_id=auth_context.request_id,
                    session_id=auth_context.session_id,
                    text=text,
                    user_id=auth_context.requester_id,
                    user_role=auth_context.role.value,
                    authorization_status=self._authorization_status(auth_context),
                    authorization_scope=sorted(auth_context.authorized_persona_ids),
                    conversation_turn=conversation_turn,
                    metadata={"prior_context": prior_context},
                )
            )
        except Exception:
            logger.exception(
                "Input Guard internal failure request_id=%s session_id=%s",
                auth_context.request_id,
                auth_context.session_id,
            )
            if not self._fail_closed:
                evidence = InputGuardEvidence(
                    enabled=True,
                    allowed=True,
                    action="WARN",
                    overall_risk_level="unknown",
                    overall_risk_score=0,
                    attack_risk_score=0,
                    access_risk_score=0,
                    primary_category="input_guard_error",
                    is_attack=False,
                    is_suspicious=True,
                    strict_runtime_monitoring=True,
                    reason_codes=["input_guard_internal_error"],
                )
                return AgentInputGuardOutcome(
                    allowed=True,
                    sanitized_text=text,
                    safe_response=None,
                    evidence=evidence,
                )

            evidence = InputGuardEvidence(
                enabled=True,
                allowed=False,
                action="BLOCK",
                overall_risk_level="critical",
                overall_risk_score=100,
                attack_risk_score=100,
                access_risk_score=0,
                primary_category="input_guard_error",
                is_attack=False,
                is_suspicious=True,
                strict_runtime_monitoring=True,
                reason_codes=["input_guard_internal_error"],
            )
            return AgentInputGuardOutcome(
                allowed=False,
                sanitized_text=None,
                safe_response="安全檢查暫時無法完成，因此這項請求尚未處理。",
                evidence=evidence,
            )

        evidence = InputGuardEvidence(
            enabled=True,
            allowed=decision.allowed,
            action=decision.action.value,
            overall_risk_level=decision.overall_risk_level,
            overall_risk_score=decision.overall_risk_score,
            attack_risk_score=decision.attack_risk_score,
            access_risk_score=decision.access_risk_score,
            primary_category=decision.primary_category,
            is_attack=decision.is_attack,
            is_suspicious=decision.is_suspicious,
            strict_runtime_monitoring=decision.strict_runtime_monitoring,
            reason_codes=decision.reason_codes,
        )
        return AgentInputGuardOutcome(
            allowed=decision.allowed,
            sanitized_text=decision.sanitized_text,
            safe_response=decision.safe_response,
            evidence=evidence,
        )

    def reset_session(self, session_id: str) -> None:
        """Clear SecretGuard's in-memory multi-turn risk signals."""
        self._service.reset_session(session_id)
