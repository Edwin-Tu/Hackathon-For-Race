"""大小寫折疊子模組（F11 一、五）。"""

from __future__ import annotations

from secretguard.common.text_utils import fold_case
from secretguard.input_normalization.normalization_result import NormalizationResult


def apply(result: NormalizationResult, text: str) -> str:
    """大小寫折疊，並記錄到 casefold_text；回傳折疊後文字供後續步驟使用。"""

    casefolded = fold_case(text)
    result.casefold_text = casefolded
    if casefolded != text:
        result.add_transformation("casefold", text, casefolded)
    return casefolded
