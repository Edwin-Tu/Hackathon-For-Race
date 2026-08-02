"""資產載入器：讀取系統預設與使用者自訂資產 JSON 檔（F13 4.2）。"""

from __future__ import annotations

import json
from pathlib import Path

from secretguard.asset_registry.asset_schema import AssetValidationError, ProtectedAsset

_POLICIES_DIR = Path(__file__).parent / "policies"
DEFAULT_ASSETS_PATH = _POLICIES_DIR / "protected_assets.json"
USER_ASSETS_PATH = _POLICIES_DIR / "user_secret_policy.json"


def _load_assets_file(path: Path) -> list[ProtectedAsset]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    assets: list[ProtectedAsset] = []
    for raw in data.get("assets", []):
        try:
            assets.append(ProtectedAsset.from_dict(raw))
        except AssetValidationError:
            # 單筆資產結構不合法時跳過該筆，不阻斷整批載入
            continue
    return assets


def load_system_assets(path: Path | None = None) -> list[ProtectedAsset]:
    """載入系統預設資產（source=system）。"""

    return _load_assets_file(path or DEFAULT_ASSETS_PATH)


def load_user_assets(path: Path | None = None) -> list[ProtectedAsset]:
    """載入使用者自訂資產（source=user）。"""

    return _load_assets_file(path or USER_ASSETS_PATH)


def save_user_assets(assets: list[ProtectedAsset], path: Path | None = None) -> None:
    """把使用者自訂資產寫回政策檔，供 CRUD 後持久化使用。"""

    target = path or USER_ASSETS_PATH
    payload = {
        "version": "1.0",
        "description": "使用者自訂資產存放檔",
        "asset_count": len(assets),
        "assets": [a.to_dict() for a in assets],
    }
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
