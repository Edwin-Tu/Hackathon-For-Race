"""語言偵測與跨語言別名子模組（F11 一：偵測語言、跨語言別名）。"""

from __future__ import annotations

import re

from secretguard.input_normalization.normalization_result import (
    NormalizationResult,
    SuspicionFlag,
)

_HAN_PATTERN = re.compile(r"[\u4e00-\u9fff]")
_HIRAGANA_KATAKANA_PATTERN = re.compile(r"[\u3040-\u30ff]")
_HANGUL_PATTERN = re.compile(r"[\uac00-\ud7a3]")
_LATIN_PATTERN = re.compile(r"[A-Za-z]")

# 跨語言別名：不同語言中指向「機密/系統提示詞/密碼」等敏感概念的詞彙，
# 用於偵測「用其他語言問同一件事」的跨語言注入手法（F09 cross_language_injection）。
CROSS_LANGUAGE_ALIASES: dict[str, list[str]] = {
    "secret": ["secret", "秘密", "機密", "秘密の", "ひみつ", "비밀"],
    "password": ["password", "密碼", "パスワード", "비밀번호"],
    "system_prompt": ["system prompt", "系統提示詞", "システムプロンプト", "시스템 프롬프트"],
    "api_key": ["api key", "api_key", "金鑰", "アピキー", "api 키"],
    "ignore_instructions": [
        "ignore previous instructions",
        "忽略之前的指令",
        "忽略先前指令",
        "以前の指示を無視",
    ],
}


def detect_languages(text: str) -> list[str]:
    """粗略偵測文字中出現的語言（依字元範圍，非精確語言辨識）。"""

    languages = []
    if _HAN_PATTERN.search(text):
        languages.append("zh")
    if _HIRAGANA_KATAKANA_PATTERN.search(text):
        languages.append("ja")
    if _HANGUL_PATTERN.search(text):
        languages.append("ko")
    if _LATIN_PATTERN.search(text):
        languages.append("en")
    return languages


def apply(result: NormalizationResult, text: str) -> None:
    """偵測語言與跨語言別名，更新 NormalizationResult。"""

    result.detected_languages = detect_languages(text)

    lowered = text.lower()
    matched = []
    for _, aliases in CROSS_LANGUAGE_ALIASES.items():
        for alias in aliases:
            if alias.lower() in lowered:
                matched.append(alias)

    if matched:
        result.matched_aliases = matched
        result.add_flag(SuspicionFlag.CROSS_LANGUAGE_ALIAS_DETECTED)
