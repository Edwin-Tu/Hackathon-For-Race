"""底層文字正規化工具，供 F11 輸入正規化與 F13 資產正規化共用。

集中放置零寬字元移除、Unicode NFKC、大小寫折疊、空白壓縮、符號移除、
相似字形（homoglyph）對應表等最基礎的字串處理，避免兩處各自實作而不一致。
"""

from __future__ import annotations

import re
import unicodedata

# 常見零寬 / 不可見字元
_ZERO_WIDTH_CHARS = [
    "\u200b",  # ZERO WIDTH SPACE
    "\u200c",  # ZERO WIDTH NON-JOINER
    "\u200d",  # ZERO WIDTH JOINER
    "\u2060",  # WORD JOINER
    "\ufeff",  # ZERO WIDTH NO-BREAK SPACE (BOM)
    "\u00ad",  # SOFT HYPHEN
]
_ZERO_WIDTH_PATTERN = re.compile("[" + "".join(_ZERO_WIDTH_CHARS) + "]")

# 常見相似字形（homoglyph）對應到標準拉丁字母，供偵測混淆使用。
HOMOGLYPH_MAP: dict[str, str] = {
    "а": "a", "А": "A",  # Cyrillic a
    "е": "e", "Е": "E",  # Cyrillic e
    "о": "o", "О": "O",  # Cyrillic o
    "р": "p", "Р": "P",  # Cyrillic p
    "с": "c", "С": "C",  # Cyrillic c
    "х": "x", "Х": "X",  # Cyrillic x
    "у": "y", "У": "Y",  # Cyrillic y
    "і": "i", "І": "I",  # Cyrillic i
    "ѕ": "s",  # Cyrillic s
    "ⅰ": "i",
    "０": "0", "１": "1", "２": "2", "３": "3", "４": "4",
    "５": "5", "６": "6", "７": "7", "８": "8", "９": "9",
    "Ａ": "A", "Ｂ": "B", "Ｃ": "C", "Ｅ": "E", "Ｉ": "I",
    "Ｏ": "O", "Ｐ": "P", "Ｓ": "S",
}

# 常見符號混淆：以符號插入在字元之間以躲避字串比對，需移除後再比對。
_OBFUSCATION_SYMBOLS_PATTERN = re.compile(r"[\-_.*·•・‧,\u00b7]")


def remove_zero_width(text: str) -> str:
    """移除零寬與不可見字元。"""

    return _ZERO_WIDTH_PATTERN.sub("", text)


def nfkc_normalize(text: str) -> str:
    """Unicode NFKC 正規化（把全角、組合字元等攤平成標準形式）。"""

    return unicodedata.normalize("NFKC", text)


def fold_case(text: str) -> str:
    """大小寫折疊（casefold，比 lower() 更嚴格，適合比對用途）。"""

    return text.casefold()


def compact_whitespace(text: str) -> str:
    """壓縮連續空白／全形空白為單一半形空白，並去除頭尾空白。"""

    text = text.replace("\u3000", " ")
    return re.sub(r"\s+", " ", text).strip()


def strip_symbols(text: str) -> str:
    """移除常見的符號混淆字元（例如 s-e-c-r-e-t 中間的分隔符）。"""

    return _OBFUSCATION_SYMBOLS_PATTERN.sub("", text)


def replace_homoglyphs(text: str) -> tuple[str, bool]:
    """把相似字形字元替換為標準拉丁字元。回傳 (替換後文字, 是否有替換)。"""

    replaced = False
    chars = []
    for ch in text:
        mapped = HOMOGLYPH_MAP.get(ch)
        if mapped is not None:
            replaced = True
            chars.append(mapped)
        else:
            chars.append(ch)
    return "".join(chars), replaced


def contains_zero_width(text: str) -> bool:
    return bool(_ZERO_WIDTH_PATTERN.search(text))


def contains_obfuscation_symbols(text: str) -> bool:
    return bool(_OBFUSCATION_SYMBOLS_PATTERN.search(text))
