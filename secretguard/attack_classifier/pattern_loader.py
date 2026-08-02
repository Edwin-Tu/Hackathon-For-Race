"""載入並編譯 attack_patterns.json 中的規則（F09 三）。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_PATTERNS_JSON_PATH = Path(__file__).parent / "attack_patterns.json"


@dataclass
class CompiledRule:
    """已編譯正規表達式的分類規則。"""

    rule_id: str
    category: str
    pattern: re.Pattern
    weight: int
    severity_hint: str
    reason: str


@lru_cache(maxsize=1)
def load_rules(path: Path | None = None) -> list[CompiledRule]:
    """載入 attack_patterns.json 並編譯每筆規則的正規表達式。"""

    target = path or _PATTERNS_JSON_PATH
    with target.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    rules: list[CompiledRule] = []
    for entry in raw.get("rules", []):
        try:
            compiled = re.compile(entry["pattern"], re.IGNORECASE)
        except re.error:
            continue
        rules.append(
            CompiledRule(
                rule_id=entry["rule_id"],
                category=entry["category"],
                pattern=compiled,
                weight=int(entry.get("weight", 10)),
                severity_hint=entry.get("severity_hint", "low"),
                reason=entry.get("reason", ""),
            )
        )
    return rules
