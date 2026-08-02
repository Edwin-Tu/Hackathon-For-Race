"""Token 守衛主體（F13 一、4.4、4.5）。

把受保護資產擴展成變體 Token，分別對「使用者輸入」與「保護提示詞」兩端做比對，
依提取意圖與教育情境決定動作（允許、警告、限制、阻擋、升級、需重寫）。
"""

from __future__ import annotations

from secretguard.asset_registry.asset_schema import ProtectedAsset
from secretguard.common.enums import TokenGuardAction
from secretguard.common.text_utils import compact_whitespace
from secretguard.token_guard.token_expander import expand_assets
from secretguard.token_guard.token_guard_result import TokenGuardResult
from secretguard.token_guard.token_matcher import match_tokens
from secretguard.token_guard.token_policy import (
    EDUCATION_KEYWORDS,
    EXTRACTION_INTENT_PATTERNS,
)

_RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _highest_risk(levels: list[str]) -> str:
    if not levels:
        return "low"
    return max(levels, key=lambda lv: _RISK_ORDER.get(lv, 0))


def _contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(kw.lower() in lowered for kw in keywords)


class RestrictedTokenGuard:
    """對輸入文字 / 保護提示詞執行限制 Token 比對與決策。"""

    def __init__(self, assets: list[ProtectedAsset]):
        self._tokens = expand_assets(assets)

    def refresh(self, assets: list[ProtectedAsset]) -> None:
        """資產新增/刪除後重新擴展 Token（F13 七之 4）。"""

        self._tokens = expand_assets(assets)

    def check_user_input(self, text: str) -> TokenGuardResult:
        """檢查使用者輸入：避免擋掉合法教學討論，同時攔截提取意圖。"""

        matches = match_tokens(text, self._tokens)
        if not matches:
            return TokenGuardResult(allowed=True, action=TokenGuardAction.ALLOW.value)

        risk_level = _highest_risk([m.risk_level for m in matches])
        has_extraction_intent = _contains_any(text, EXTRACTION_INTENT_PATTERNS)
        is_educational = _contains_any(text, EDUCATION_KEYWORDS)

        reasons = [f"命中 {len(matches)} 筆限制 Token" for _ in [0]]
        matched_asset_ids = sorted({m.asset_id for m in matches})
        reasons.append(f"涉及資產: {', '.join(matched_asset_ids)}")

        if is_educational and not has_extraction_intent:
            # 純教育性討論且無提取動詞：降級為允許或警告
            action = TokenGuardAction.ALLOW.value if risk_level in ("low", "medium") else TokenGuardAction.WARN.value
            allowed = action == TokenGuardAction.ALLOW.value
            reasons.append("偵測到教育情境關鍵字，且無提取意圖動詞，予以降級")
            return TokenGuardResult(
                allowed=allowed,
                action=action,
                risk_level=risk_level,
                matches=matches,
                restricted_tokens=[t for t in self._tokens if t.asset_id in matched_asset_ids],
                reasons=reasons,
            )

        if has_extraction_intent:
            reasons.append("偵測到提取/揭露意圖動詞")
            if risk_level == "critical":
                action = TokenGuardAction.BLOCK.value
            elif risk_level == "high":
                action = TokenGuardAction.ESCALATE.value
            else:
                action = TokenGuardAction.RESTRICT.value
            return TokenGuardResult(
                allowed=False,
                action=action,
                risk_level=risk_level,
                matches=matches,
                restricted_tokens=[t for t in self._tokens if t.asset_id in matched_asset_ids],
                reasons=reasons,
            )

        # 無明顯提取意圖，但仍命中敏感 Token：以風險等級決定警告或限制
        if risk_level in ("critical", "high"):
            action = TokenGuardAction.RESTRICT.value
            allowed = False
        else:
            action = TokenGuardAction.WARN.value
            allowed = True
        return TokenGuardResult(
            allowed=allowed,
            action=action,
            risk_level=risk_level,
            matches=matches,
            restricted_tokens=[t for t in self._tokens if t.asset_id in matched_asset_ids],
            reasons=reasons,
        )

    def check_protected_prompt(self, prompt: str) -> TokenGuardResult:
        """檢查即將送進模型的保護提示詞：任何命中都視為嚴重問題（需重寫或 critical）。"""

        matches = match_tokens(prompt, self._tokens)
        if not matches:
            return TokenGuardResult(allowed=True, action=TokenGuardAction.ALLOW.value)

        risk_level = _highest_risk([m.risk_level for m in matches])
        matched_asset_ids = sorted({m.asset_id for m in matches})
        reasons = [
            "保護提示詞中出現資產原始值/部分值/別名，屬嚴重設計缺陷",
            f"涉及資產: {', '.join(matched_asset_ids)}",
        ]
        exact_leak = any(m.match_type == "exact" for m in matches)
        action = (
            TokenGuardAction.BLOCK.value
            if exact_leak or risk_level == "critical"
            else TokenGuardAction.REWRITE_REQUIRED.value
        )
        return TokenGuardResult(
            allowed=False,
            action=action,
            risk_level=risk_level if exact_leak or risk_level == "critical" else "critical",
            matches=matches,
            restricted_tokens=[t for t in self._tokens if t.asset_id in matched_asset_ids],
            reasons=reasons,
        )

    def sanitize(self, text: str, placeholder: str = "[REDACTED]") -> str:
        """把命中的限制 Token 以佔位字取代，回傳處理後文字（供 sanitized_prompt 使用）。"""

        matches = match_tokens(text, self._tokens)
        if not matches:
            return text
        result = text
        # 依 matched_text 長度由長到短取代，避免短片段先取代破壞長片段比對
        seen_texts = sorted(
            {m.matched_text for m in matches if m.matched_text},
            key=len,
            reverse=True,
        )
        for matched_text in seen_texts:
            if matched_text:
                result = result.replace(matched_text, placeholder)
        return compact_whitespace(result)
