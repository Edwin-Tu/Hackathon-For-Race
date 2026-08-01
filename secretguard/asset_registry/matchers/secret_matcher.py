"""機密值比對器：完全、大小寫不敏感、別名、部分、編碼比對（F13 4.3）。"""

from __future__ import annotations

import base64
import binascii

from secretguard.asset_registry.asset_match import AssetMatch
from secretguard.asset_registry.asset_normalizer import normalize_for_matching
from secretguard.asset_registry.asset_schema import ProtectedAsset
from secretguard.common.enums import ProtectionMode

# 部分比對最小長度：避免太短的片段（例如單一字元）造成大量誤判
_MIN_PARTIAL_LEN = 6


def _try_decode_candidates(text: str) -> list[str]:
    """嘗試把文字當作常見編碼解碼，回傳解碼候選（含原文）。"""

    candidates = [text]
    stripped = text.strip()
    # Base64
    try:
        padded = stripped + "=" * (-len(stripped) % 4)
        decoded = base64.b64decode(padded, validate=False)
        candidates.append(decoded.decode("utf-8", errors="ignore"))
    except (binascii.Error, ValueError):
        pass
    # Hex
    try:
        if len(stripped) % 2 == 0 and all(
            c in "0123456789abcdefABCDEF" for c in stripped
        ):
            candidates.append(bytes.fromhex(stripped).decode("utf-8", errors="ignore"))
    except ValueError:
        pass
    return candidates


def match_secret(text: str, asset: ProtectedAsset) -> list[AssetMatch]:
    """對單一資產執行機密值比對，回傳所有命中結果（可能為多筆）。"""

    matches: list[AssetMatch] = []
    if not asset.enabled:
        return matches

    modes = set(asset.protection_modes)
    norm_text = normalize_for_matching(text)
    norm_value = normalize_for_matching(asset.value)

    # exact_match（大小寫敏感原文比對）
    if ProtectionMode.EXACT_MATCH.value in modes and asset.value in text:
        matches.append(
            AssetMatch(
                asset_id=asset.asset_id,
                asset_name=asset.name,
                match_type=ProtectionMode.EXACT_MATCH.value,
                risk_level=asset.risk_level,
                matched_text=asset.value,
                confidence=1.0,
                reason="文字中出現資產原始值",
            )
        )

    # case_insensitive_match
    if (
        ProtectionMode.CASE_INSENSITIVE_MATCH.value in modes
        and norm_value
        and norm_value in norm_text
        and not any(m.match_type == ProtectionMode.EXACT_MATCH.value for m in matches)
    ):
        matches.append(
            AssetMatch(
                asset_id=asset.asset_id,
                asset_name=asset.name,
                match_type=ProtectionMode.CASE_INSENSITIVE_MATCH.value,
                risk_level=asset.risk_level,
                matched_text=asset.value,
                confidence=0.95,
                reason="正規化後（含大小寫折疊）比對到資產值",
            )
        )

    # alias_match
    if ProtectionMode.ALIAS_MATCH.value in modes:
        for alias in asset.aliases:
            norm_alias = normalize_for_matching(alias)
            if norm_alias and norm_alias in norm_text:
                matches.append(
                    AssetMatch(
                        asset_id=asset.asset_id,
                        asset_name=asset.name,
                        match_type=ProtectionMode.ALIAS_MATCH.value,
                        risk_level=asset.risk_level,
                        matched_text=alias,
                        confidence=0.6,
                        reason=f"文字提及資產別名「{alias}」",
                    )
                )

    # partial_match：資產值長度足夠時，取子字串片段比對
    if (
        ProtectionMode.PARTIAL_MATCH.value in modes
        and len(norm_value) >= _MIN_PARTIAL_LEN
    ):
        window = _MIN_PARTIAL_LEN
        for i in range(0, len(norm_value) - window + 1):
            fragment = norm_value[i : i + window]
            if fragment in norm_text:
                matches.append(
                    AssetMatch(
                        asset_id=asset.asset_id,
                        asset_name=asset.name,
                        match_type=ProtectionMode.PARTIAL_MATCH.value,
                        risk_level=asset.risk_level,
                        matched_text=fragment,
                        confidence=0.7,
                        reason="文字中出現資產值的部分片段",
                    )
                )
                break

    # encoding_match：嘗試解碼文字後是否命中資產值
    if ProtectionMode.ENCODING_MATCH.value in modes:
        for candidate in _try_decode_candidates(text):
            if candidate == text:
                continue
            if asset.value in candidate or norm_value in normalize_for_matching(
                candidate
            ):
                matches.append(
                    AssetMatch(
                        asset_id=asset.asset_id,
                        asset_name=asset.name,
                        match_type=ProtectionMode.ENCODING_MATCH.value,
                        risk_level=asset.risk_level,
                        matched_text=candidate[:64],
                        confidence=0.85,
                        reason="解碼後文字命中資產值",
                    )
                )
                break

    return matches
