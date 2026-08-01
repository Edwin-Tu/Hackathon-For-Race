"""重建比對器：偵測使用者是否嘗試把資產值拆片段、加分隔符後重新組回原值。

例如「s-e-c-r-e-t」、「s e c r e t」、逆序、逐字元列出等重建攻擊模式。
"""

from __future__ import annotations

from secretguard.asset_registry.asset_match import AssetMatch
from secretguard.asset_registry.asset_normalizer import normalize_for_matching
from secretguard.asset_registry.asset_schema import ProtectedAsset
from secretguard.common.enums import ProtectionMode
from secretguard.common.text_utils import strip_symbols


def match_reconstruction(text: str, asset: ProtectedAsset) -> list[AssetMatch]:
    """偵測資產值是否以「拆解＋分隔符」的形式藏在文字中。"""

    matches: list[AssetMatch] = []
    if not asset.enabled:
        return matches
    if ProtectionMode.RECONSTRUCTION_MATCH.value not in asset.protection_modes:
        return matches

    norm_value = normalize_for_matching(asset.value)
    if len(norm_value) < 4:
        return matches

    # 去除符號混淆後再比對（e.g. "s-e-c-r-e-t" -> "secret"）
    stripped = strip_symbols(text)
    norm_stripped = normalize_for_matching(stripped)
    if norm_value in norm_stripped and norm_value not in normalize_for_matching(text):
        matches.append(
            AssetMatch(
                asset_id=asset.asset_id,
                asset_name=asset.name,
                match_type=ProtectionMode.RECONSTRUCTION_MATCH.value,
                risk_level=asset.risk_level,
                matched_text=stripped[:64],
                confidence=0.8,
                reason="移除分隔符號後可重建出資產值，疑似拆解攻擊",
            )
        )

    # 逆序重建：資產值反轉後出現在文字中
    reversed_value = norm_value[::-1]
    if reversed_value in norm_stripped:
        matches.append(
            AssetMatch(
                asset_id=asset.asset_id,
                asset_name=asset.name,
                match_type=ProtectionMode.RECONSTRUCTION_MATCH.value,
                risk_level=asset.risk_level,
                matched_text=reversed_value[:64],
                confidence=0.75,
                reason="文字中出現資產值的逆序形式",
            )
        )

    return matches
