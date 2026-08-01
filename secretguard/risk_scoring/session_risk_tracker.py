"""會話風險追蹤（F10 4.4：SessionRiskTracker）。

輸入為會話訊號列表，輸出累計分數與高風險訊號（分數大於等於門檻者）。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from secretguard.risk_scoring.score_calculator import clamp_score, score_session_signal

# 高風險訊號門檻：單一訊號分數達到此值即列入 high_risk_signals。
HIGH_RISK_SIGNAL_THRESHOLD = 20


@dataclass
class SessionRiskAssessment:
    """會話風險評估結果。"""

    total_score: int
    high_risk_signals: list[str] = field(default_factory=list)
    all_signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_score": self.total_score,
            "high_risk_signals": self.high_risk_signals,
            "all_signals": self.all_signals,
        }


class SessionRiskTracker:
    """追蹤單一會話累積的風險訊號並計算累計分數。"""

    def __init__(self) -> None:
        self._signals: list[str] = []

    def add_signal(self, signal: str) -> None:
        self._signals.append(signal)

    def add_signals(self, signals: list[str]) -> None:
        self._signals.extend(signals)

    def reset(self) -> None:
        self._signals.clear()

    def assess(self) -> SessionRiskAssessment:
        """計算目前累積訊號的總分與高風險訊號清單。"""

        total = 0
        high_risk = []
        for signal in self._signals:
            score = score_session_signal(signal)
            total += score
            if score >= HIGH_RISK_SIGNAL_THRESHOLD and signal not in high_risk:
                high_risk.append(signal)

        return SessionRiskAssessment(
            total_score=clamp_score(total),
            high_risk_signals=high_risk,
            all_signals=list(self._signals),
        )


def assess_signals(signals: list[str]) -> SessionRiskAssessment:
    """無狀態版本：直接對一組訊號計算評估結果，不需維護 tracker 實例。"""

    tracker = SessionRiskTracker()
    tracker.add_signals(signals)
    return tracker.assess()
