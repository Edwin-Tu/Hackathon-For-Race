"""重建模式偵測子模組（F11 一：偵測重建模式，如逐字元列出、拼接指示等）。"""

from __future__ import annotations

import re

from secretguard.input_normalization.normalization_result import (
    NormalizationResult,
    SuspicionFlag,
)

# 常見重建攻擊指示語句：要求模型「逐字元」、「一個一個」輸出或拼接內容。
_RECONSTRUCTION_HINTS = [
    r"逐字元", r"一個一個(字|輸出)", r"分開.{0,6}(輸出|列出|寫出)",
    r"每個字元", r"character by character", r"letter by letter",
    r"spell (it |them )?out", r"one character at a time",
    r"拆開.{0,6}(寫|說|輸出)",
]
_RECONSTRUCTION_PATTERN = re.compile("|".join(_RECONSTRUCTION_HINTS), re.IGNORECASE)

# 帶分隔符的逐字排列（例如 s-e-c-r-e-t 或 s.e.c.r.e.t），長度 >=4 字元才視為可疑。
_SPACED_LETTERS_PATTERN = re.compile(
    r"\b(?:[A-Za-z][\-_.\s]){3,}[A-Za-z]\b"
)


def apply(result: NormalizationResult, text: str) -> None:
    """偵測文字是否包含重建攻擊模式，更新可疑旗標。"""

    if _RECONSTRUCTION_PATTERN.search(text) or _SPACED_LETTERS_PATTERN.search(text):
        result.add_flag(SuspicionFlag.RECONSTRUCTION_PATTERN_DETECTED)
