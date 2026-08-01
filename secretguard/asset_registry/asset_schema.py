"""受保護資產結構與驗證（F13 4.1、4.3）。"""

from __future__ import annotations

from dataclasses import dataclass, field

from secretguard.common.enums import AssetRiskLevel, ProtectionMode

_VALID_RISK_LEVELS = {r.value for r in AssetRiskLevel}
_VALID_PROTECTION_MODES = {p.value for p in ProtectionMode}


class AssetValidationError(ValueError):
    """資產結構驗證失敗。"""


@dataclass
class ProtectedAsset:
    """受保護資產（F13 4.1）。"""

    asset_id: str
    value: str
    name: str = ""
    type: str = "secret"
    aliases: list[str] = field(default_factory=list)
    risk_level: str = AssetRiskLevel.MEDIUM.value
    allowed_roles: list[str] = field(default_factory=lambda: ["owner"])
    protection_modes: list[str] = field(
        default_factory=lambda: [
            ProtectionMode.EXACT_MATCH.value,
            ProtectionMode.CASE_INSENSITIVE_MATCH.value,
            ProtectionMode.ALIAS_MATCH.value,
            ProtectionMode.PARTIAL_MATCH.value,
        ]
    )
    enabled: bool = True
    description: str = ""
    source: str = "system"

    def __post_init__(self) -> None:
        if not self.asset_id:
            raise AssetValidationError("asset_id 為必填欄位")
        if not self.value:
            raise AssetValidationError(f"資產 {self.asset_id} 缺少 value")
        if self.risk_level not in _VALID_RISK_LEVELS:
            raise AssetValidationError(
                f"資產 {self.asset_id} 的 risk_level 不合法: {self.risk_level}"
            )
        invalid_modes = set(self.protection_modes) - _VALID_PROTECTION_MODES
        if invalid_modes:
            raise AssetValidationError(
                f"資產 {self.asset_id} 含不合法 protection_modes: {invalid_modes}"
            )
        if self.source not in {"system", "user"}:
            raise AssetValidationError(
                f"資產 {self.asset_id} 的 source 必須是 system 或 user"
            )
        if not self.name:
            self.name = self.asset_id

    @classmethod
    def from_dict(cls, data: dict) -> "ProtectedAsset":
        return cls(
            asset_id=data["asset_id"],
            value=data["value"],
            name=data.get("name", ""),
            type=data.get("type", "secret"),
            aliases=list(data.get("aliases", [])),
            risk_level=data.get("risk_level", AssetRiskLevel.MEDIUM.value),
            allowed_roles=list(data.get("allowed_roles", ["owner"])),
            protection_modes=list(
                data.get(
                    "protection_modes",
                    [
                        ProtectionMode.EXACT_MATCH.value,
                        ProtectionMode.CASE_INSENSITIVE_MATCH.value,
                    ],
                )
            ),
            enabled=data.get("enabled", True),
            description=data.get("description", ""),
            source=data.get("source", "system"),
        )

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "name": self.name,
            "type": self.type,
            "value": self.value,
            "aliases": self.aliases,
            "risk_level": self.risk_level,
            "allowed_roles": self.allowed_roles,
            "protection_modes": self.protection_modes,
            "enabled": self.enabled,
            "description": self.description,
            "source": self.source,
        }

    def has_mode(self, mode: str | ProtectionMode) -> bool:
        mode_value = mode.value if isinstance(mode, ProtectionMode) else mode
        return mode_value in self.protection_modes
