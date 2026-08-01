"""載入 token_rules.json 與 token_risk_map.json（F13 4.6）。"""

from __future__ import annotations

import json
from pathlib import Path
from functools import lru_cache

_POLICIES_DIR = Path(__file__).parent / "policies"
TOKEN_RULES_PATH = _POLICIES_DIR / "token_rules.json"
TOKEN_RISK_MAP_PATH = _POLICIES_DIR / "token_risk_map.json"

# 教育情境白名單關鍵字：出現時降低動作嚴重度，避免擋掉一般教學討論（F13 七之 3）。
EDUCATION_KEYWORDS = [
    "什麼是", "教學", "範例", "example", "教我", "解釋", "原理",
    "how does", "explain", "教育目的", "概念",
]

# 提取意圖樣式：搭配 Token 類別關鍵字出現時視為高風險提取嘗試。
EXTRACTION_INTENT_PATTERNS = [
    "告訴我", "洩漏", "揭露", "說出", "透露", "給我", "顯示", "print",
    "reveal", "tell me", "show me", "leak", "disclose", "give me", "輸出",
    "忽略之前", "ignore previous", "ignore all previous",
]


@lru_cache(maxsize=1)
def load_token_rules() -> dict[str, list[str]]:
    with TOKEN_RULES_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_token_risk_map() -> dict[str, str]:
    with TOKEN_RISK_MAP_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def risk_level_for_token(token: str) -> str:
    """查詢單個 Token/別名對應的風險等級，找不到時預設 low。"""

    risk_map = load_token_risk_map()
    return risk_map.get(token.lower(), risk_map.get(token, "low"))
