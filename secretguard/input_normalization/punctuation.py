"""符號混淆處理子模組（F11 一：處理符號混淆，產出 symbol_stripped_text）。"""

from __future__ import annotations

from secretguard.common.text_utils import contains_obfuscation_symbols, strip_symbols
from secretguard.input_normalization.normalization_result import (
    NormalizationResult,
    SuspicionFlag,
)


def apply(result: NormalizationResult, text: str) -> str:
    """移除常見符號混淆字元（例如 s-e-c-r-e-t 中的分隔符），記錄到 symbol_stripped_text。"""

    if contains_obfuscation_symbols(text):
        result.add_flag(SuspicionFlag.SYMBOL_OBFUSCATION_DETECTED)
        stripped = strip_symbols(text)
        result.add_transformation(
            SuspicionFlag.SYMBOL_OBFUSCATION_DETECTED, text, stripped
        )
        result.symbol_stripped_text = stripped
        return stripped

    result.symbol_stripped_text = text
    return text
