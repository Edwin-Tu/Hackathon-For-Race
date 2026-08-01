"""輸入正規化主流程（F11 五：資料流與處理順序）。

處理順序（依規格文件）：
1. 空白壓縮
2. Unicode 正規化（NFKC）+ 相似字形替換
3. 大小寫折疊
4. 符號移除
（零寬字元移除已併入空白處理前的前置步驟，因為編碼探測必須在字元移除之後進行）
5. 編碼探測（必須在零寬字元/符號移除之後，避免破壞可疑模式）
6. 別名偵測（跨語言）
7. 重建模式偵測
"""

from __future__ import annotations

from secretguard.common.text_utils import remove_zero_width
from secretguard.input_normalization import (
    case,
    encoding_probe,
    language_hint_detector,
    punctuation,
    reconstruction_normalizer,
    unicode_norm,
    whitespace,
)
from secretguard.input_normalization.normalization_result import (
    NormalizationResult,
    SuspicionFlag,
)


def normalize(text: str) -> NormalizationResult:
    """對原始輸入文字執行完整正規化流程，回傳 NormalizationResult。"""

    result = NormalizationResult(raw_text=text)

    # 前置：移除零寬字元（必須在編碼探測之前，避免零寬字元破壞編碼樣式比對）
    working = text
    no_zw = remove_zero_width(working)
    if no_zw != working:
        result.add_flag(SuspicionFlag.ZERO_WIDTH_CHARACTER_REMOVED)
        result.add_transformation(
            SuspicionFlag.ZERO_WIDTH_CHARACTER_REMOVED, working, no_zw
        )
    working = no_zw

    # 1. 空白壓縮
    working = whitespace.apply(result, working)

    # 2. Unicode 正規化（NFKC + 相似字形）
    working = unicode_norm.apply(result, working)

    # 3. 大小寫折疊（獨立產出 casefold_text，不覆蓋主線 working，
    #    因為後續符號移除／編碼探測仍需保留原始大小寫供某些規則比對）
    case.apply(result, working)

    # 4. 符號移除（產出 symbol_stripped_text）
    punctuation.apply(result, working)

    result.compact_text = working
    result.normalized_text = working

    # 5. 編碼探測：必須在字元移除之後進行，避免零寬/符號干擾編碼樣式
    result.decoded_candidates = encoding_probe.apply(result, working)

    # 6. 跨語言別名與語言偵測
    language_hint_detector.apply(result, working)

    # 7. 重建模式偵測（同時檢查原文與符號移除後文字，因為重建模式常依賴符號分隔）
    reconstruction_normalizer.apply(result, text)
    reconstruction_normalizer.apply(result, result.symbol_stripped_text)

    return result
