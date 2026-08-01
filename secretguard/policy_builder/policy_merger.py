"""政策合併器：把政策決定、資產、技能執行結果合併進 RequestProtectionPolicy 的輔助函式。"""

from __future__ import annotations

from secretguard.common.enums import ProtectionMode


def merge_protection_modes(matched_assets: list[dict]) -> list[str]:
    """彙整所有命中資產宣告的防護模式（去重）。"""

    modes: set[str] = set()
    for asset in matched_assets:
        modes.update(asset.get("protection_modes", []))
    if not modes:
        modes = {ProtectionMode.EXACT_MATCH.value, ProtectionMode.CASE_INSENSITIVE_MATCH.value}
    return sorted(modes)


def merge_asset_fields(matched_assets: list[dict]) -> tuple[list[str], list[str], list[str]]:
    """彙整資產 ID、名稱、型別（去重，保持原順序）。"""

    ids, names, types = [], [], []
    for asset in matched_assets:
        aid = asset.get("asset_id")
        name = asset.get("name") or asset.get("asset_name")
        atype = asset.get("type")
        if aid and aid not in ids:
            ids.append(aid)
        if name and name not in names:
            names.append(name)
        if atype and atype not in types:
            types.append(atype)
    return ids, names, types


def merge_enabled_skills(required_skills: list[str], executed_skills: list[str]) -> list[str]:
    """彙整必要技能與實際執行技能（去重，保持順序）。"""

    merged = []
    for skill in [*required_skills, *executed_skills]:
        if skill and skill not in merged:
            merged.append(skill)
    return merged
