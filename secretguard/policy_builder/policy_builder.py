"""政策建構器主體（F10 一、六之 4）。

把 PolicyDecision 與資產、技能結果合併成 RequestProtectionPolicy
（資產保護範圍、回應範圍、技能、限制 Token、輸出驗證旗標、運行監控模式）。
"""

from __future__ import annotations

import uuid

from secretguard.common.enums import PolicyAction, ProtectionMode
from secretguard.policy_builder.policy_merger import (
    merge_asset_fields,
    merge_enabled_skills,
    merge_protection_modes,
)
from secretguard.policy_builder.policy_models import RequestProtectionPolicy
from secretguard.policy_builder.role_policy_resolver import resolve_allowed_scope
from secretguard.policy_builder.scope_builder import build_allowed_scope, build_denied_scope
from secretguard.policy_engine.policy_decision import PolicyDecision

# 輸出驗證旗標對應：政策動作越嚴重，啟用越多驗證模式（呼應 F10 4.8、F12 對外介面）。
_ACTION_VERIFY_MODES = {
    PolicyAction.ALLOW.value: set(),
    PolicyAction.WARN.value: {ProtectionMode.EXACT_MATCH.value},
    PolicyAction.REWRITE.value: {ProtectionMode.EXACT_MATCH.value, ProtectionMode.PARTIAL_MATCH.value},
    PolicyAction.RESTRICT.value: {
        ProtectionMode.EXACT_MATCH.value,
        ProtectionMode.PARTIAL_MATCH.value,
        ProtectionMode.ENCODING_MATCH.value,
    },
    PolicyAction.AUTHORIZE.value: {
        ProtectionMode.EXACT_MATCH.value,
        ProtectionMode.PARTIAL_MATCH.value,
        ProtectionMode.ENCODING_MATCH.value,
    },
    PolicyAction.ESCALATE.value: {
        ProtectionMode.EXACT_MATCH.value,
        ProtectionMode.PARTIAL_MATCH.value,
        ProtectionMode.ENCODING_MATCH.value,
        ProtectionMode.RECONSTRUCTION_MATCH.value,
        ProtectionMode.TRANSLATION_MATCH.value,
    },
    PolicyAction.BLOCK.value: {
        ProtectionMode.EXACT_MATCH.value,
        ProtectionMode.PARTIAL_MATCH.value,
        ProtectionMode.ENCODING_MATCH.value,
        ProtectionMode.RECONSTRUCTION_MATCH.value,
        ProtectionMode.TRANSLATION_MATCH.value,
    },
}

_INTERRUPT_ACTIONS = {PolicyAction.BLOCK.value, PolicyAction.ESCALATE.value, PolicyAction.AUTHORIZE.value}

# 常見安全替代建議，依攻擊類別提供，避免每次都是同一句拒絕語。
_SAFE_ALTERNATIVES = [
    "可以請管理員透過授權管道申請存取受保護資訊。",
    "可以詢問一般性概念，例如「什麼是 API 金鑰」而非要求提供實際數值。",
]


def build_request_protection_policy(
    decision: PolicyDecision,
    matched_assets: list[dict] | None = None,
    executed_skills: list[str] | None = None,
    user_role: str = "guest",
    attack_category: str | None = None,
    request_id: str | None = None,
) -> RequestProtectionPolicy:
    """依政策決定與其他上下文建構 RequestProtectionPolicy。"""

    matched_assets = matched_assets or []
    executed_skills = executed_skills or []

    asset_ids, asset_names, asset_types = merge_asset_fields(matched_assets)
    protection_modes = merge_protection_modes(matched_assets)
    enabled_skills = merge_enabled_skills(decision.required_skills, executed_skills)

    role_allowed_scope = resolve_allowed_scope(user_role)
    allowed_scope = build_allowed_scope(decision.action, role_allowed_scope)
    denied_scope = build_denied_scope(decision.action)

    verify_modes = _ACTION_VERIFY_MODES.get(decision.action, set())

    return RequestProtectionPolicy(
        request_id=request_id or str(uuid.uuid4()),
        action=decision.action,
        risk_score=decision.risk_score,
        risk_level=decision.risk_level,
        user_role=user_role,
        attack_category=attack_category,
        protected_asset_ids=asset_ids,
        protected_asset_names=asset_names,
        protected_asset_types=asset_types,
        protection_modes=protection_modes,
        allowed_response_scope=allowed_scope,
        denied_response_scope=denied_scope,
        blocked_disclosure_types=list(denied_scope),
        enabled_skills=enabled_skills,
        restricted_tokens=[],
        blocked_transformations=(
            ["base64_encode", "translate", "reverse", "char_split"]
            if decision.action in _INTERRUPT_ACTIONS
            else []
        ),
        require_authorization=decision.action == PolicyAction.AUTHORIZE.value
        or decision.should_block,
        runtime_monitoring_enabled=decision.action != PolicyAction.ALLOW.value,
        runtime_monitoring_mode=decision.monitoring_level,
        interrupt_on_match=decision.action in _INTERRUPT_ACTIONS,
        output_verification_enabled=bool(verify_modes),
        verify_exact=ProtectionMode.EXACT_MATCH.value in verify_modes,
        verify_partial=ProtectionMode.PARTIAL_MATCH.value in verify_modes,
        verify_encoding=ProtectionMode.ENCODING_MATCH.value in verify_modes,
        verify_translation=ProtectionMode.TRANSLATION_MATCH.value in verify_modes,
        verify_reconstruction=ProtectionMode.RECONSTRUCTION_MATCH.value in verify_modes,
        refusal_strategy="polite_decline" if decision.action != PolicyAction.BLOCK.value else "firm_refusal",
        safe_alternatives=_SAFE_ALTERNATIVES if decision.should_block else [],
        metadata={"policy_reason": decision.reason},
    )
