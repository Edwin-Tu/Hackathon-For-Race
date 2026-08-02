"""Unicode 正規化子模組（F11 一：NFKC 正規化與相似字形偵測）。"""

from __future__ import annotations

from secretguard.common.text_utils import nfkc_normalize, replace_homoglyphs
from secretguard.input_normalization.normalization_result import (
    NormalizationResult,
    SuspicionFlag,
)


def apply(result: NormalizationResult, text: str) -> str:
    """NFKC 正規化後偵測並替換相似字形，回傳處理後文字。"""

    nfkc_text = nfkc_normalize(text)
    if nfkc_text != text:
        result.add_transformation("nfkc_normalize", text, nfkc_text)
    text = nfkc_text

    replaced_text, had_homoglyph = replace_homoglyphs(text)
    if had_homoglyph:
        result.add_flag(SuspicionFlag.UNICODE_CONFUSABLE_DETECTED)
        result.add_transformation(
            SuspicionFlag.UNICODE_CONFUSABLE_DETECTED, text, replaced_text
        )
        text = replaced_text

    return text
