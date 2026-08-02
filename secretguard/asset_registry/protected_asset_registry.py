"""受保護資產註冊表（F13 一、二）：合併系統與使用者資產，提供 CRUD、搜尋與比對。"""

from __future__ import annotations

from pathlib import Path

from secretguard.asset_registry import asset_loader
from secretguard.asset_registry.asset_match import AssetMatch
from secretguard.asset_registry.asset_normalizer import normalize_for_matching
from secretguard.asset_registry.asset_schema import ProtectedAsset
from secretguard.asset_registry.matchers.reconstruction_matcher import (
    match_reconstruction,
)
from secretguard.asset_registry.matchers.secret_matcher import match_secret
from secretguard.asset_registry.matchers.semantic_matcher import match_semantic
from secretguard.asset_registry.matchers.translation_matcher import match_translation


class AssetNotFoundError(KeyError):
    """指定的 asset_id 不存在於註冊表中。"""


class ProtectedAssetRegistry:
    """受保護資產註冊表：系統預設資產與使用者資產目錄的單一入口。"""

    def __init__(
        self,
        system_assets: list[ProtectedAsset] | None = None,
        user_assets: list[ProtectedAsset] | None = None,
        user_assets_path: Path | None = None,
    ) -> None:
        self._user_assets_path = user_assets_path or asset_loader.USER_ASSETS_PATH
        self._assets: dict[str, ProtectedAsset] = {}
        for asset in system_assets if system_assets is not None else asset_loader.load_system_assets():
            self._assets[asset.asset_id] = asset
        for asset in user_assets if user_assets is not None else asset_loader.load_user_assets(
            self._user_assets_path
        ):
            self._assets[asset.asset_id] = asset

    # ---------- CRUD ----------

    def add_asset(self, asset: ProtectedAsset, persist: bool = True) -> None:
        """新增（或覆寫）一筆使用者資產，預設立即持久化到 user_secret_policy.json。"""

        self._assets[asset.asset_id] = asset
        if persist:
            self._persist_user_assets()

    def remove_asset(self, asset_id: str, persist: bool = True) -> None:
        if asset_id not in self._assets:
            raise AssetNotFoundError(asset_id)
        del self._assets[asset_id]
        if persist:
            self._persist_user_assets()

    def get_asset(self, asset_id: str) -> ProtectedAsset:
        if asset_id not in self._assets:
            raise AssetNotFoundError(asset_id)
        return self._assets[asset_id]

    def list_assets(self, enabled_only: bool = True) -> list[ProtectedAsset]:
        assets = list(self._assets.values())
        if enabled_only:
            assets = [a for a in assets if a.enabled]
        return assets

    def _persist_user_assets(self) -> None:
        user_assets = [a for a in self._assets.values() if a.source == "user"]
        asset_loader.save_user_assets(user_assets, self._user_assets_path)

    # ---------- 搜尋 ----------

    def search(self, keyword: str) -> list[ProtectedAsset]:
        """依名稱、型別、別名、說明關鍵字搜尋資產。"""

        norm_keyword = normalize_for_matching(keyword)
        results = []
        for asset in self._assets.values():
            haystacks = [asset.name, asset.type, asset.description, *asset.aliases]
            if any(norm_keyword in normalize_for_matching(h) for h in haystacks if h):
                results.append(asset)
        return results

    # ---------- 比對 ----------

    def match_text(
        self, text: str, enabled_only: bool = True
    ) -> list[AssetMatch]:
        """對文字執行全部資產、全部比對模式的秘密比對，回傳所有命中結果。"""

        matches: list[AssetMatch] = []
        for asset in self.list_assets(enabled_only=enabled_only):
            matches.extend(match_secret(text, asset))
            matches.extend(match_reconstruction(text, asset))
            matches.extend(match_semantic(text, asset))
            matches.extend(match_translation(text, asset))
        return matches

    def match_asset(self, text: str, asset_id: str) -> list[AssetMatch]:
        """僅針對單一資產執行比對。"""

        asset = self.get_asset(asset_id)
        matches: list[AssetMatch] = []
        matches.extend(match_secret(text, asset))
        matches.extend(match_reconstruction(text, asset))
        matches.extend(match_semantic(text, asset))
        matches.extend(match_translation(text, asset))
        return matches

    # ---------- 執行期匯出（供 F13 五之 6：流式監控使用） ----------

    def export_runtime_tokens(self) -> dict[str, dict]:
        """把每個資產匯出成 exact/partial/aliases/encoded/normalized 與 risk_level 結構。"""

        export: dict[str, dict] = {}
        for asset in self.list_assets(enabled_only=True):
            norm_value = normalize_for_matching(asset.value)
            export[asset.asset_id] = {
                "exact": asset.value,
                "partial": [norm_value[i : i + 6] for i in range(0, max(len(norm_value) - 5, 0), 6)],
                "aliases": list(asset.aliases),
                "normalized": norm_value,
                "risk_level": asset.risk_level,
            }
        return export
