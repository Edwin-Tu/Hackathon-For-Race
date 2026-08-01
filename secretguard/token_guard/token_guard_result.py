"""TokenMatch 與 TokenGuardResult 結構（F13 4.5）。"""

from __future__ import annotations

from dataclasses import dataclass, field

from secretguard.common.enums import TokenGuardAction, TokenSource, TokenType


@dataclass
class RestrictedToken:
    """限制 Token（F13 4.4）。"""

    asset_id: str
    token: str
    token_type: str
    risk_level: str
    source: str

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "token_present": bool(self.token),
            "token_length": len(self.token),
            "token_type": self.token_type,
            "risk_level": self.risk_level,
            "source": self.source,
        }


@dataclass
class TokenMatch:
    """單筆 Token 命中結果（F13 4.5）。"""

    asset_id: str
    matched_text: str
    match_type: str
    risk_level: str
    start: int = -1
    end: int = -1
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "matched": bool(self.matched_text),
            "matched_length": len(self.matched_text),
            "match_type": self.match_type,
            "risk_level": self.risk_level,
            "start": self.start,
            "end": self.end,
            "reason": self.reason,
        }


@dataclass
class TokenGuardResult:
    """Token 守衛結果（F13 4.5）。"""

    allowed: bool
    action: str = TokenGuardAction.ALLOW.value
    risk_level: str = "low"
    matches: list[TokenMatch] = field(default_factory=list)
    restricted_tokens: list[RestrictedToken] = field(default_factory=list)
    sanitized_prompt: str | None = None
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "action": self.action,
            "risk_level": self.risk_level,
            "matches": [m.to_dict() for m in self.matches],
            "restricted_tokens": [t.to_dict() for t in self.restricted_tokens],
            "sanitized_prompt": self.sanitized_prompt,
            "reasons": self.reasons,
        }
