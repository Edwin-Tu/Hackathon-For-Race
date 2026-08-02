"""語意比對器：不比對原文字面，改比對「意圖是否指向該資產」的關鍵詞。

沒有嵌入模型的情況下，以資產名稱/型別/別名的語意關鍵詞加上揭露動詞
（告訴我、洩漏、reveal、tell me 等）共同出現作為輕量級語意訊號。
"""

from __future__ import annotations

from secretguard.asset_registry.asset_match import AssetMatch
from secretguard.asset_registry.asset_normalizer import normalize_for_matching
from secretguard.asset_registry.asset_schema import ProtectedAsset
from secretguard.common.enums import ProtectionMode

_DISCLOSURE_VERBS = [
    "告訴我", "洩漏", "揭露", "說出", "透露", "給我", "顯示",
    "reveal", "tell me", "show me", "leak", "disclose", "give me", "print",
]


def match_semantic(text: str, asset: ProtectedAsset) -> list[AssetMatch]:
    """偵測文字是否同時提及資產語意關鍵詞與揭露類動詞。"""

    matches: list[AssetMatch] = []
    if not asset.enabled:
        return matches
    if ProtectionMode.SEMANTIC_MATCH.value not in asset.protection_modes:
        return matches

    norm_text = normalize_for_matching(text)

    semantic_terms = [asset.name, asset.type, *asset.aliases]
    matched_term = None
    for term in semantic_terms:
        norm_term = normalize_for_matching(term)
        if norm_term and norm_term in norm_text:
            matched_term = term
            break
    if matched_term is None:
        return matches

    matched_verb = None
    for verb in _DISCLOSURE_VERBS:
        if normalize_for_matching(verb) in norm_text:
            matched_verb = verb
            break
    if matched_verb is None:
        return matches

    matches.append(
        AssetMatch(
            asset_id=asset.asset_id,
            asset_name=asset.name,
            match_type=ProtectionMode.SEMANTIC_MATCH.value,
            risk_level=asset.risk_level,
            matched_text=f"{matched_term} + {matched_verb}",
            confidence=0.55,
            reason=f"語意上同時出現資產指涉詞「{matched_term}」與揭露動詞「{matched_verb}」",
        )
    )
    return matches
