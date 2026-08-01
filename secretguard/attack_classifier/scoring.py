"""分類評分邏輯：把命中規則彙整為信心分數與嚴重度（F09 四）。"""

from __future__ import annotations

from secretguard.attack_classifier.result import MatchedRule

_SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}

# 信心分數換算：權重總和除以此常數後夾在 0~1，數值可依實測調整。
_CONFIDENCE_SCALE = 60.0


def aggregate_category_scores(matched_rules: list[MatchedRule]) -> dict[str, int]:
    """把命中規則依類別加總權重。"""

    scores: dict[str, int] = {}
    for rule in matched_rules:
        scores[rule.category] = scores.get(rule.category, 0) + rule.weight
    return scores


def pick_primary_category(category_scores: dict[str, int]) -> str:
    """挑選總分最高的類別；無命中時回傳 benign。"""

    if not category_scores:
        return "benign"
    return max(category_scores.items(), key=lambda kv: kv[1])[0]


def compute_confidence(total_weight: int) -> float:
    """把總權重轉換為 0~1 信心分數。"""

    confidence = total_weight / _CONFIDENCE_SCALE
    return round(min(max(confidence, 0.0), 1.0), 3)


def aggregate_severity(matched_rules: list[MatchedRule], primary_category: str) -> str:
    """取該類別下命中規則的最高嚴重度；無命中回傳 low。"""

    relevant = [r for r in matched_rules if r.category == primary_category]
    if not relevant:
        return "low"
    return max(relevant, key=lambda r: _SEVERITY_ORDER.get(r.severity_hint, 0)).severity_hint
