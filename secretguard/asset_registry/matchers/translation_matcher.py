"""翻譯比對器：偵測要求「用其他語言重述/翻譯」機密的繞過手法。

實務上完整跨語言比對需要翻譯引擎，這裡以「翻譯類動詞 + 資產指涉詞」的共現
作為輕量訊號，並保留擴充點供未來接上翻譯 API 做真正的跨語言字面比對。
"""

from __future__ import annotations

from secretguard.asset_registry.asset_match import AssetMatch
from secretguard.asset_registry.asset_normalizer import normalize_for_matching
from secretguard.asset_registry.asset_schema import ProtectedAsset
from secretguard.common.enums import ProtectionMode

_TRANSLATION_VERBS = [
    "翻譯", "translate", "用英文說", "用日文說", "in english", "in japanese",
    "用法文", "in french", "換一種語言", "用其他語言",
]


def match_translation(text: str, asset: ProtectedAsset) -> list[AssetMatch]:
    """偵測文字是否要求以翻譯手段繞過對資產的直接揭露限制。"""

    matches: list[AssetMatch] = []
    if not asset.enabled:
        return matches
    if ProtectionMode.TRANSLATION_MATCH.value not in asset.protection_modes:
        return matches

    norm_text = normalize_for_matching(text)

    matched_verb = None
    for verb in _TRANSLATION_VERBS:
        if normalize_for_matching(verb) in norm_text:
            matched_verb = verb
            break
    if matched_verb is None:
        return matches

    semantic_terms = [asset.name, asset.type, *asset.aliases]
    matched_term = None
    for term in semantic_terms:
        norm_term = normalize_for_matching(term)
        if norm_term and norm_term in norm_text:
            matched_term = term
            break
    if matched_term is None:
        return matches

    matches.append(
        AssetMatch(
            asset_id=asset.asset_id,
            asset_name=asset.name,
            match_type=ProtectionMode.TRANSLATION_MATCH.value,
            risk_level=asset.risk_level,
            matched_text=f"{matched_verb} + {matched_term}",
            confidence=0.5,
            reason=f"疑似以翻譯手段（{matched_verb}）繞過對「{matched_term}」的限制",
        )
    )
    return matches
