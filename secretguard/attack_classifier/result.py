"""Attack-classification result structures."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MatchedRule:
    rule_id: str
    category: str
    severity_hint: str
    weight: int
    reason: str
    matched_fragments: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        # Do not serialize prompt fragments: they can contain credentials or personal data.
        return {
            "rule_id": self.rule_id,
            "category": self.category,
            "severity_hint": self.severity_hint,
            "weight": self.weight,
            "reason": self.reason,
            "matched_fragment_count": len(self.matched_fragments),
        }


@dataclass
class AttackClassificationResult:
    is_attack: bool
    primary_category: str = "benign"
    matched_categories: list[str] = field(default_factory=list)
    confidence: float = 0.0
    severity_hint: str = "low"
    matched_rules: list[MatchedRule] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    recommended_skill: str | None = None
    notes: str = ""
    is_suspicious: bool = False

    def to_dict(self) -> dict:
        return {
            "is_attack": self.is_attack,
            "is_suspicious": self.is_suspicious,
            "primary_category": self.primary_category,
            "matched_categories": self.matched_categories,
            "confidence": self.confidence,
            "severity_hint": self.severity_hint,
            "matched_rules": [r.to_dict() for r in self.matched_rules],
            "evidence_count": len(self.evidence),
            "recommended_skill": self.recommended_skill,
            "notes": self.notes,
        }
