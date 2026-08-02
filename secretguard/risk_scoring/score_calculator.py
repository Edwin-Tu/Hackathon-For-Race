"""評分計算細節：意圖分數表與各面向分數計算（F10 4.2、4.3）。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_SCORING_RULES_PATH = Path(__file__).parent / "scoring_rules.json"

# F10 4.3：意圖資產參照分數。
INTENT_ASSET_REFERENCE_SCORES = {
    "no_asset_reference": 0,
    "asset_value_reference": 35,
    "protected_registry_match": 50,
}

# F10 4.3：意圖操作分數。
INTENT_OPERATION_SCORES = {
    "EXPLAIN": -10,
    "DISCLOSE": 60,
    "EXTRACT": 70,
    "RECONSTRUCT": 75,
    "TRANSFORM": 75,
}

# F10 4.3：意圖範圍分數。
INTENT_SCOPE_SCORES = {
    "GENERAL_CONCEPT": -15,
    "CURRENT_SYSTEM": 50,
    "PROTECTED_REGISTRY": 70,
}

# F10 4.3：揭露模式分數。
DISCLOSURE_MODE_SCORES = {
    "NONE": 0,
    "FULL_VALUE": 60,
    "ENCODED_VALUE": 65,
    "RECONSTRUCTED_VALUE": 70,
}


@lru_cache(maxsize=1)
def load_scoring_rules(path: Path | None = None) -> dict:
    target = path or _SCORING_RULES_PATH
    with target.open("r", encoding="utf-8") as f:
        return json.load(f)


def score_attack_category(category: str | None) -> int:
    rules = load_scoring_rules()
    return int(rules["attack_category_scores"].get(category or "benign", 0))


def score_asset_risk(risk_level: str) -> int:
    rules = load_scoring_rules()
    return int(rules["asset_risk_scores"].get(risk_level, 0))


def score_match_type(match_type: str) -> int:
    rules = load_scoring_rules()
    return int(rules["match_type_scores"].get(match_type, 0))


def score_authorization(status: str) -> int:
    rules = load_scoring_rules()
    return int(rules["authorization_adjustments"].get(status, 0))


def score_session_signal(signal: str) -> int:
    rules = load_scoring_rules()
    return int(rules["session_signal_scores"].get(signal, 0))


def score_intent(
    asset_reference_type: str | None,
    operation: str | None,
    scope: str | None,
    disclosure_mode: str | None,
) -> int:
    """把四個意圖欄位分數加總（F10 4.3）。"""

    total = 0
    total += INTENT_ASSET_REFERENCE_SCORES.get(asset_reference_type or "no_asset_reference", 0)
    total += INTENT_OPERATION_SCORES.get(operation or "", 0)
    total += INTENT_SCOPE_SCORES.get(scope or "", 0)
    total += DISCLOSURE_MODE_SCORES.get(disclosure_mode or "NONE", 0)
    return total


def risk_level_for_score(score: int) -> str:
    """依 thresholds 表把分數對應到風險等級。"""

    rules = load_scoring_rules()
    thresholds: dict[str, list[int]] = rules["thresholds"]
    for level, (low, high) in thresholds.items():
        if low <= score <= high:
            return level
    return "critical" if score > 100 else "low"


def action_for_risk_level(risk_level: str) -> str:
    """依風險等級對應建議政策動作（F10 五：風險門檻對應）。"""

    mapping = {
        "low": "ALLOW",
        "moderate": "WARN",
        "medium": "REWRITE",
        "high": "RESTRICT",
        "critical": "BLOCK",
    }
    return mapping.get(risk_level, "WARN")


def clamp_score(score: int) -> int:
    """把分數夾在 0~100（F10 八之 1）。"""

    return max(0, min(100, score))
