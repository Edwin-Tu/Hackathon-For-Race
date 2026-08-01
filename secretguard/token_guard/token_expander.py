"""把受保護資產擴展成各種變體 Token（完全、部分、別名、編碼、正規化）（F13 一、4.4）。

七之 2：擴展 Token 需有上限，避免記憶體與比對成本失控。
"""

from __future__ import annotations

import base64

from secretguard.asset_registry.asset_normalizer import normalize_for_matching
from secretguard.asset_registry.asset_schema import ProtectedAsset
from secretguard.common.enums import TokenSource, TokenType
from secretguard.token_guard.token_guard_result import RestrictedToken

# 單一資產擴展出的 Token 數量上限，避免變體爆炸。
MAX_TOKENS_PER_ASSET = 32
# 部分片段的滑動視窗長度與最小資產長度門檻。
_PARTIAL_WINDOW = 6
_PARTIAL_MIN_LEN = 8
# 每個資產最多產生的部分片段數量，避免長資產產生過多片段。
_MAX_PARTIAL_FRAGMENTS = 10


def expand_asset(asset: ProtectedAsset) -> list[RestrictedToken]:
    """把單一資產擴展為限制 Token 清單，數量不超過 MAX_TOKENS_PER_ASSET。"""

    tokens: list[RestrictedToken] = []

    # exact
    tokens.append(
        RestrictedToken(
            asset_id=asset.asset_id,
            token=asset.value,
            token_type=TokenType.EXACT.value,
            risk_level=asset.risk_level,
            source=TokenSource.ASSET_VALUE.value,
        )
    )

    # normalized
    norm_value = normalize_for_matching(asset.value)
    if norm_value != asset.value:
        tokens.append(
            RestrictedToken(
                asset_id=asset.asset_id,
                token=norm_value,
                token_type=TokenType.NORMALIZED.value,
                risk_level=asset.risk_level,
                source=TokenSource.GENERATED_VARIANT.value,
            )
        )

    # alias
    for alias in asset.aliases:
        if len(tokens) >= MAX_TOKENS_PER_ASSET:
            break
        tokens.append(
            RestrictedToken(
                asset_id=asset.asset_id,
                token=alias,
                token_type=TokenType.ALIAS.value,
                risk_level=asset.risk_level,
                source=TokenSource.ALIAS.value,
            )
        )

    # partial：滑動視窗切片，數量受上限控制
    if len(norm_value) >= _PARTIAL_MIN_LEN:
        fragment_count = 0
        step = max(_PARTIAL_WINDOW, len(norm_value) // _MAX_PARTIAL_FRAGMENTS or 1)
        for i in range(0, len(norm_value) - _PARTIAL_WINDOW + 1, step):
            if (
                len(tokens) >= MAX_TOKENS_PER_ASSET
                or fragment_count >= _MAX_PARTIAL_FRAGMENTS
            ):
                break
            fragment = norm_value[i : i + _PARTIAL_WINDOW]
            tokens.append(
                RestrictedToken(
                    asset_id=asset.asset_id,
                    token=fragment,
                    token_type=TokenType.PARTIAL.value,
                    risk_level=asset.risk_level,
                    source=TokenSource.GENERATED_VARIANT.value,
                )
            )
            fragment_count += 1

    # encoded：base64 編碼變體（僅取一種代表性編碼，避免爆炸）
    if len(tokens) < MAX_TOKENS_PER_ASSET:
        try:
            encoded = base64.b64encode(asset.value.encode("utf-8")).decode("ascii")
            tokens.append(
                RestrictedToken(
                    asset_id=asset.asset_id,
                    token=encoded,
                    token_type=TokenType.ENCODED.value,
                    risk_level=asset.risk_level,
                    source=TokenSource.GENERATED_VARIANT.value,
                )
            )
        except Exception:
            pass

    return tokens[:MAX_TOKENS_PER_ASSET]


def expand_assets(assets: list[ProtectedAsset]) -> list[RestrictedToken]:
    """批次擴展多個資產。"""

    result: list[RestrictedToken] = []
    for asset in assets:
        if not asset.enabled:
            continue
        result.extend(expand_asset(asset))
    return result
