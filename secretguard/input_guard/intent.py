"""Deterministic request-intent inference for Input Guard policy decisions."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IntentResult:
    operation: str | None
    scope: str | None
    disclosure_mode: str | None
    asset_reference_type: str | None
    educational_context: bool
    execution_intent: bool
    cross_scope_request: bool


_EDUCATIONAL = re.compile(
    r"(?:什麼是|解釋|說明|分析|分類|檢查|測試|範例|如何|防止|避免|僅做翻譯|不要執行|勿執行|"
    r"單元測試|原理|比較|review|classify|explain|analy[sz]e|security|防禦|緩解)",
    re.IGNORECASE,
)
_EXECUTION = re.compile(
    r"(?:執行|遵照|照做|依照.*命令|只(?:要)?輸出|直接輸出|立即執行|回覆\s*CANARY|print\s+CANARY|"
    r"follow\s+(?:it|them|the instruction)|obey|do exactly|不要拒絕|never refuse)",
    re.IGNORECASE,
)
_EXTRACT = re.compile(
    r"(?:顯示|列出|輸出|告訴|透露|揭露|貼出|匯出|回顯|重複|引用|dump|reveal|show|print|"
    r"tell me|give me|return|echo|repeat|export)",
    re.IGNORECASE,
)
_SENSITIVE = re.compile(
    r"(?:密碼|password|api\s*key|access\s*token|token|secret|credential|private\s*key|私鑰|"
    r"身分證|病歷|住民資料|medical\s*record|resident\s*data|system\s*prompt|developer\s*(?:prompt|instructions)|"
    r"hidden\s*(?:prompt|instructions)|內部規則|系統提示詞|初始指令)",
    re.IGNORECASE,
)
_PARTIAL = re.compile(
    r"(?:前\s*\d+|後\s*\d+|第一個字|下一個字|前綴|後綴|總長度|逐字|一個字元|"
    r"prefix|suffix|first\s+\w+|last\s+\w+|character\s+count|one character)",
    re.IGNORECASE,
)
_TRANSFORM = re.compile(
    r"(?:base64|十六進位|hex|url\s*encod|倒序|反向|摩斯|morse|翻譯成|translate|json|yaml)",
    re.IGNORECASE,
)
_CURRENT_SYSTEM = re.compile(
    r"(?:目前|現在|你的|此系統|目前對話|system\s*prompt|developer\s*(?:prompt|instructions)|"
    r"hidden\s*(?:prompt|instructions)|internal\s*(?:prompt|rules|configuration)|系統提示詞|內部規則)",
    re.IGNORECASE,
)
_CROSS_SCOPE = re.compile(
    r"(?:其他住民|所有住民|上一位使用者|其他使用者|其他家庭成員|不屬於我|跨\s*tenant|"
    r"other\s+(?:users?|residents?|tenants?)|last\s+\w+\s+users?|another\s+user)",
    re.IGNORECASE,
)


def infer_intent(text: str, has_asset_match: bool = False) -> IntentResult:
    educational = bool(_EDUCATIONAL.search(text))
    execution = bool(_EXECUTION.search(text))
    sensitive = bool(_SENSITIVE.search(text))
    extraction = bool(_EXTRACT.search(text))
    partial = bool(_PARTIAL.search(text))
    transform = bool(_TRANSFORM.search(text))
    current_system = bool(_CURRENT_SYSTEM.search(text))
    cross_scope = bool(_CROSS_SCOPE.search(text))

    operation: str | None = None
    disclosure_mode: str | None = "NONE"
    if partial and sensitive:
        operation = "RECONSTRUCT"
        disclosure_mode = "RECONSTRUCTED_VALUE"
    elif transform and sensitive and extraction:
        operation = "TRANSFORM"
        disclosure_mode = "ENCODED_VALUE"
    elif sensitive and extraction:
        operation = "EXTRACT"
        disclosure_mode = "FULL_VALUE"
    elif educational and not execution:
        operation = "EXPLAIN"

    scope: str | None = None
    if educational and not execution and not (sensitive and extraction):
        scope = "GENERAL_CONCEPT"
    elif current_system:
        scope = "CURRENT_SYSTEM"
    elif sensitive or has_asset_match:
        scope = "PROTECTED_REGISTRY"

    asset_reference_type = (
        "protected_registry_match"
        if has_asset_match
        else "asset_value_reference"
        if sensitive
        else "no_asset_reference"
    )

    return IntentResult(
        operation=operation,
        scope=scope,
        disclosure_mode=disclosure_mode,
        asset_reference_type=asset_reference_type,
        educational_context=educational,
        execution_intent=execution,
        cross_scope_request=cross_scope,
    )
