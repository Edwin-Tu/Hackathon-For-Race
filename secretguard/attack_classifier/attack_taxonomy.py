"""攻擊類別目錄載入（F09 4.2：attacks.json 結構）。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

_ATTACKS_JSON_PATH = Path(__file__).parent / "attacks.json"


@dataclass
class AttackCategory:
    """攻擊類別目錄項目（F09 4.2）。"""

    category_id: str
    name: str
    description: str
    risk_level: str
    patterns: list[str] = field(default_factory=list)
    mitigation: str = ""

    @property
    def mitigation_skills(self) -> list[str]:
        """把逗號分隔的 mitigation 字串拆成技能清單。"""

        if not self.mitigation:
            return []
        return [s.strip() for s in self.mitigation.split(",") if s.strip()]


@lru_cache(maxsize=1)
def load_attack_taxonomy(path: Path | None = None) -> dict[str, AttackCategory]:
    """載入攻擊類別目錄，回傳 category_id -> AttackCategory 的對應表。"""

    target = path or _ATTACKS_JSON_PATH
    with target.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    taxonomy: dict[str, AttackCategory] = {}
    for category_id, data in raw.items():
        taxonomy[category_id] = AttackCategory(
            category_id=category_id,
            name=data.get("name", category_id),
            description=data.get("description", ""),
            risk_level=data.get("risk_level", "low"),
            patterns=list(data.get("patterns", [])),
            mitigation=data.get("mitigation", ""),
        )
    return taxonomy


def get_category(category_id: str) -> AttackCategory | None:
    return load_attack_taxonomy().get(category_id)
