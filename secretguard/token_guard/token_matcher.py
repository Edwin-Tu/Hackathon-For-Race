"""在文字中比對限制 Token 清單，產生 TokenMatch 列表（F13 4.5）。"""

from __future__ import annotations

from secretguard.asset_registry.asset_normalizer import normalize_for_matching
from secretguard.token_guard.token_guard_result import RestrictedToken, TokenMatch


def match_tokens(text: str, tokens: list[RestrictedToken]) -> list[TokenMatch]:
    """在文字中尋找限制 Token 出現的位置，回傳所有命中結果。"""

    matches: list[TokenMatch] = []
    norm_text = normalize_for_matching(text)

    for tok in tokens:
        if not tok.token:
            continue
        norm_token = normalize_for_matching(tok.token)
        if not norm_token:
            continue

        # 先用正規化文字比對（涵蓋大小寫、全形、相似字形等混淆）
        idx = norm_text.find(norm_token)
        if idx != -1:
            matches.append(
                TokenMatch(
                    asset_id=tok.asset_id,
                    matched_text=tok.token,
                    match_type=tok.token_type,
                    risk_level=tok.risk_level,
                    start=idx,
                    end=idx + len(norm_token),
                    reason=f"命中限制 Token（{tok.token_type}）",
                )
            )
            continue

        # 原文精確比對（處理正規化可能改變長度導致位置失準的情況）
        raw_idx = text.find(tok.token)
        if raw_idx != -1:
            matches.append(
                TokenMatch(
                    asset_id=tok.asset_id,
                    matched_text=tok.token,
                    match_type=tok.token_type,
                    risk_level=tok.risk_level,
                    start=raw_idx,
                    end=raw_idx + len(tok.token),
                    reason=f"原文命中限制 Token（{tok.token_type}）",
                )
            )

    return matches
