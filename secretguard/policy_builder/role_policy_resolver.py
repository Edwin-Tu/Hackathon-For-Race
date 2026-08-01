"""角色政策解析器：依使用者角色決定基礎回應範圍與是否需要授權。"""

from __future__ import annotations

# 角色 -> 允許回應範圍（一般性描述，實際資產仍受 scope_builder 進一步限制）。
_ROLE_ALLOWED_SCOPE = {
    "owner": ["full_access", "explain_concepts", "system_metadata"],
    "admin": ["explain_concepts", "system_metadata", "limited_asset_reference"],
    "authenticated_user": ["explain_concepts"],
    "guest": ["explain_concepts"],
    "anonymous": ["explain_concepts"],
}

_TRUSTED_ROLES = {"owner", "admin"}


def resolve_allowed_scope(user_role: str) -> list[str]:
    return list(_ROLE_ALLOWED_SCOPE.get(user_role, _ROLE_ALLOWED_SCOPE["guest"]))


def is_trusted_role(user_role: str) -> bool:
    return user_role in _TRUSTED_ROLES
