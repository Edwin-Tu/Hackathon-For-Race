"""SecretGuard 共用列舉。

集中定義 F09~F13 文件中反覆出現的列舉型別，避免各模組各自定義造成不一致。
所有列舉皆繼承 str，方便序列化（JSON/dict）與跨模組比較。
"""

from __future__ import annotations

from enum import Enum


class PolicyAction(str, Enum):
    """政策 / 技能 / 路由共用的動作列舉（F09 4.5、F10 4.5）。"""

    ALLOW = "ALLOW"
    WARN = "WARN"
    REWRITE = "REWRITE"
    RESTRICT = "RESTRICT"
    AUTHORIZE = "AUTHORIZE"
    ESCALATE = "ESCALATE"
    BLOCK = "BLOCK"


# F09 4.5：動作嚴重度排序（由低到高）。多技能合併時取最高嚴重度動作。
ACTION_SEVERITY: dict[PolicyAction, int] = {
    PolicyAction.ALLOW: 0,
    PolicyAction.WARN: 1,
    PolicyAction.REWRITE: 2,
    PolicyAction.RESTRICT: 3,
    PolicyAction.AUTHORIZE: 4,
    PolicyAction.ESCALATE: 5,
    PolicyAction.BLOCK: 6,
}


def max_severity_action(actions: list[PolicyAction]) -> PolicyAction:
    """回傳一組動作中嚴重度最高者；空清單回傳 ALLOW。"""

    if not actions:
        return PolicyAction.ALLOW
    return max(actions, key=lambda a: ACTION_SEVERITY.get(a, 0))


class RiskLevel(str, Enum):
    """風險評分等級（F10 4.1）。"""

    LOW = "low"
    MODERATE = "moderate"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MonitoringLevel(str, Enum):
    """運行監控等級（F10 五）。"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LogLevel(str, Enum):
    """記錄等級（F10 五）。"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class AssetRiskLevel(str, Enum):
    """受保護資產風險等級（F13 4.1）。"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProtectionMode(str, Enum):
    """資產防護 / 比對模式（F13 4.3）。"""

    EXACT_MATCH = "exact_match"
    CASE_INSENSITIVE_MATCH = "case_insensitive_match"
    ALIAS_MATCH = "alias_match"
    PARTIAL_MATCH = "partial_match"
    ENCODING_MATCH = "encoding_match"
    SEMANTIC_MATCH = "semantic_match"
    TRANSLATION_MATCH = "translation_match"
    RECONSTRUCTION_MATCH = "reconstruction_match"


class TokenType(str, Enum):
    """限制 Token 型別（F13 4.4）。"""

    EXACT = "exact"
    PARTIAL = "partial"
    ALIAS = "alias"
    ENCODED = "encoded"
    NORMALIZED = "normalized"


class TokenSource(str, Enum):
    """限制 Token 來源（F13 4.4）。"""

    ASSET_VALUE = "asset_value"
    ALIAS = "alias"
    GENERATED_VARIANT = "generated_variant"
    POLICY = "policy"


class TokenGuardAction(str, Enum):
    """Token 守衛動作（F13 4.5）。"""

    ALLOW = "ALLOW"
    WARN = "WARN"
    RESTRICT = "RESTRICT"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"
    REWRITE_REQUIRED = "REWRITE_REQUIRED"


class OutputSeverity(str, Enum):
    """輸出守衛嚴重度（F12 4.4）。"""

    NO_LEAK = "NO_LEAK"
    LOW_RISK_HINT = "LOW_RISK_HINT"
    PARTIAL_LEAK = "PARTIAL_LEAK"
    FULL_LEAK = "FULL_LEAK"
    CRITICAL_LEAK = "CRITICAL_LEAK"


class OutputAction(str, Enum):
    """輸出守衛動作（F12 4.4）。"""

    ALLOW = "ALLOW"
    REDACT = "REDACT"
    BLOCK = "BLOCK"
    REWRITE = "REWRITE"
    ESCALATE = "ESCALATE"


class LeakType(str, Enum):
    """洩漏類型（F12 4.8）。"""

    FULL_LEAK = "FULL_LEAK"
    PARTIAL_LEAK = "PARTIAL_LEAK"
    ENCODING_LEAK = "ENCODING_LEAK"
    RECONSTRUCTION_LEAK = "RECONSTRUCTION_LEAK"
    TRANSLATION_LEAK = "TRANSLATION_LEAK"
    SEMANTIC_LEAK = "SEMANTIC_LEAK"
    NO_LEAK = "NO_LEAK"


# F12 4.8：洩漏類型到建議動作的對應。
LEAK_TYPE_ACTION: dict[LeakType, OutputAction] = {
    LeakType.FULL_LEAK: OutputAction.BLOCK,
    LeakType.ENCODING_LEAK: OutputAction.BLOCK,
    LeakType.RECONSTRUCTION_LEAK: OutputAction.BLOCK,
    LeakType.PARTIAL_LEAK: OutputAction.REDACT,
    LeakType.TRANSLATION_LEAK: OutputAction.REDACT,
    LeakType.SEMANTIC_LEAK: OutputAction.REDACT,
    LeakType.NO_LEAK: OutputAction.ALLOW,
}

# F12 4.4：嚴重度到動作的對應。
SEVERITY_ACTION: dict[OutputSeverity, OutputAction] = {
    OutputSeverity.NO_LEAK: OutputAction.ALLOW,
    OutputSeverity.LOW_RISK_HINT: OutputAction.ALLOW,
    OutputSeverity.PARTIAL_LEAK: OutputAction.REDACT,
    OutputSeverity.FULL_LEAK: OutputAction.REDACT,
    OutputSeverity.CRITICAL_LEAK: OutputAction.BLOCK,
}


class MatchType(str, Enum):
    """風險評分使用的比對型別（F10 4.2 match_type_scores）。"""

    EXACT_MATCH = "exact_match"
    ENCODING_MATCH = "encoding_match"
    RECONSTRUCTION_MATCH = "reconstruction_match"
    PARTIAL_MATCH = "partial_match"
    ALIAS_MATCH = "alias_match"
    SEMANTIC_MATCH = "semantic_match"
    TRANSLATION_MATCH = "translation_match"


class AuthorizationStatus(str, Enum):
    """授權狀態（F10 4.2 authorization_adjustments）。"""

    OWNER = "owner"
    AUTHORIZED = "authorized"
    UNAUTHORIZED = "unauthorized"
    ROLE_CLAIM_ONLY = "role_claim_only"


class IntentOperation(str, Enum):
    """意圖操作分類（F10 4.3）。"""

    EXPLAIN = "EXPLAIN"
    DISCLOSE = "DISCLOSE"
    EXTRACT = "EXTRACT"
    RECONSTRUCT = "RECONSTRUCT"
    TRANSFORM = "TRANSFORM"


class IntentScope(str, Enum):
    """意圖範圍分類（F10 4.3）。"""

    GENERAL_CONCEPT = "GENERAL_CONCEPT"
    CURRENT_SYSTEM = "CURRENT_SYSTEM"
    PROTECTED_REGISTRY = "PROTECTED_REGISTRY"


class DisclosureMode(str, Enum):
    """揭露模式分類（F10 4.3）。"""

    NONE = "NONE"
    FULL_VALUE = "FULL_VALUE"
    ENCODED_VALUE = "ENCODED_VALUE"
    RECONSTRUCTED_VALUE = "RECONSTRUCTED_VALUE"


class AssetReferenceType(str, Enum):
    """意圖資產參照型別（F10 4.3）。"""

    NO_ASSET_REFERENCE = "no_asset_reference"
    ASSET_VALUE_REFERENCE = "asset_value_reference"
    PROTECTED_REGISTRY_MATCH = "protected_registry_match"
