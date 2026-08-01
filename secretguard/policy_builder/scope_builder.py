"""回應範圍建構器：依政策動作與資產決定允許/禁止回應範圍與被阻擋的揭露型別。"""

from __future__ import annotations

from secretguard.common.enums import PolicyAction

# 動作 -> 禁止揭露型別（動作越嚴重，禁止的揭露型別越多）。
_ACTION_BLOCKED_DISCLOSURE_TYPES = {
    PolicyAction.ALLOW.value: [],
    PolicyAction.WARN.value: ["full_secret_value"],
    PolicyAction.REWRITE.value: ["full_secret_value", "encoded_secret_value"],
    PolicyAction.RESTRICT.value: [
        "full_secret_value",
        "partial_secret_value",
        "encoded_secret_value",
    ],
    PolicyAction.AUTHORIZE.value: [
        "full_secret_value",
        "partial_secret_value",
        "encoded_secret_value",
    ],
    PolicyAction.ESCALATE.value: [
        "full_secret_value",
        "partial_secret_value",
        "encoded_secret_value",
        "reconstructed_secret_value",
    ],
    PolicyAction.BLOCK.value: [
        "full_secret_value",
        "partial_secret_value",
        "encoded_secret_value",
        "reconstructed_secret_value",
        "translated_secret_value",
    ],
}


def build_denied_scope(action: str) -> list[str]:
    return list(_ACTION_BLOCKED_DISCLOSURE_TYPES.get(action, []))


def build_allowed_scope(action: str, role_allowed_scope: list[str]) -> list[str]:
    """依動作嚴重度過濾角色允許範圍：BLOCK/ESCALATE 時只保留概念性說明。"""

    if action in (PolicyAction.BLOCK.value, PolicyAction.ESCALATE.value):
        return [s for s in role_allowed_scope if s == "explain_concepts"] or [
            "explain_concepts"
        ]
    return list(role_allowed_scope)
