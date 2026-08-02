"""空白混淆處理子模組（F11 一：處理空白混淆）。"""

from __future__ import annotations

from secretguard.common.text_utils import compact_whitespace
from secretguard.input_normalization.normalization_result import (
    NormalizationResult,
    SuspicionFlag,
)


def apply(result: NormalizationResult, text: str) -> str:
    """壓縮連續/全形空白為單一半形空白，回傳處理後文字；同時更新可疑旗標與轉換紀錄。"""

    compacted = compact_whitespace(text)
    if compacted != text:
        result.add_flag(SuspicionFlag.SPACING_OBFUSCATION_DETECTED)
        result.add_transformation(
            SuspicionFlag.SPACING_OBFUSCATION_DETECTED, text, compacted
        )
        text = compacted

    return text
