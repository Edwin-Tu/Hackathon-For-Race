"""資產正規化（F13 一：NFKC、相似字形、零寬字元）。"""

from __future__ import annotations

from secretguard.common.text_utils import (
    fold_case,
    nfkc_normalize,
    remove_zero_width,
    replace_homoglyphs,
)


def normalize_for_matching(text: str) -> str:
    """把任意文字正規化為用於資產比對的標準形式。

    處理順序：先移除零寬字元，NFKC 正規化，替換相似字形，最後大小寫折疊。
    這個順序確保混淆技巧被攤平之後才進行字形替換與比對。
    """

    text = remove_zero_width(text)
    text = nfkc_normalize(text)
    text, _ = replace_homoglyphs(text)
    text = fold_case(text)
    return text
