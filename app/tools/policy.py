"""
Confirmation policy and permission checking.

Confirmation is required for:
- medication events
- high importance reminders
- medical-related reminders (hospital, medication keywords)
- All modify/delete operations (when implemented)
"""

import hashlib
import secrets
import time
from dataclasses import dataclass, field
from typing import Any

from app.tools.enums import EventType, Importance, Role
from app.tools.models import AuthContext, ToolCall


@dataclass
class PendingConfirmation:
    """
    A pending confirmation waiting for user approval.
    
    Stores complete ToolCall so confirmation doesn't need
    to re-accept arguments from client (prevents tampering).
    """

    token: str
    request_id: str
    session_id: str
    tool_call: ToolCall
    target_persona_id: str | None
    arguments_hash: str
    created_at: float
    expires_at: float
    summary: str
    consumed: bool = False


class ConfirmationStore:
    """
    In-memory store for pending confirmations.
    
    Stores complete ToolCall server-side so that:
    1. confirm_and_execute doesn't accept arguments from client
    2. Token is single-use
    3. Arguments cannot be tampered with after confirmation request
    
    TODO: Replace with Redis or database for production.
    """

    DEFAULT_TTL_SECONDS = 300  # 5 minutes

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self._store: dict[str, PendingConfirmation] = {}
        self._ttl_seconds = ttl_seconds

    def create(
        self,
        request_id: str,
        session_id: str,
        tool_call: ToolCall,
        validated_args: dict[str, Any],
        target_persona_id: str | None,
        summary: str,
    ) -> str:
        """
        Create a confirmation token and store pending confirmation.
        
        Stores the complete ToolCall so it can be executed later
        without accepting new arguments from the client.
        """
        token = secrets.token_urlsafe(32)
        now = time.time()

        # Hash arguments for verification
        args_str = str(sorted(validated_args.items()))
        args_hash = hashlib.sha256(args_str.encode()).hexdigest()

        pending = PendingConfirmation(
            token=token,
            request_id=request_id,
            session_id=session_id,
            tool_call=tool_call,
            target_persona_id=target_persona_id,
            arguments_hash=args_hash,
            created_at=now,
            expires_at=now + self._ttl_seconds,
            summary=summary,
            consumed=False,
        )
        self._store[token] = pending
        self._cleanup_expired()
        return token

    def get_pending(
        self,
        token: str,
        session_id: str,
    ) -> tuple[PendingConfirmation | None, str]:
        """
        Get pending confirmation by token.
        
        Returns (pending, error_message).
        Does NOT consume the token - use consume() after successful execution.
        """
        self._cleanup_expired()

        pending = self._store.get(token)
        if pending is None:
            return None, "確認代碼無效或已過期"

        # Check if already consumed (single-use)
        if pending.consumed:
            return None, "確認代碼已使用"

        # Check expiration
        if time.time() > pending.expires_at:
            del self._store[token]
            return None, "確認代碼已過期，請重新操作"

        # Check session matches
        if pending.session_id != session_id:
            return None, "確認代碼與目前工作階段不符"

        return pending, ""

    def consume(self, token: str) -> bool:
        """
        Mark token as consumed (single-use).
        
        Returns True if successfully consumed, False if not found.
        """
        pending = self._store.get(token)
        if pending is None:
            return False
        pending.consumed = True
        # Remove from store after consumption
        del self._store[token]
        return True

    def _cleanup_expired(self) -> None:
        """Remove expired confirmations."""
        now = time.time()
        expired = [k for k, v in self._store.items() if now > v.expires_at]
        for k in expired:
            del self._store[k]


class PermissionPolicy:
    """
    Permission checking based on role and persona scope.
    
    Rules:
    - resident: can only access active_persona_id
    - caregiver: can only access authorized_persona_ids
    - family: read-only, can only access authorized_persona_ids
    - admin: can access all (in demo), still audited
    - system: based on explicit backend configuration
    """

    @staticmethod
    def check_write_permission(
        auth_context: AuthContext,
        tool_name: str,
        target_persona_id: str | None,
    ) -> tuple[bool, str]:
        """
        Check if auth context has write permission for target persona.
        
        Returns (allowed, error_message).
        """
        role = auth_context.role

        # Family cannot write
        if role == Role.FAMILY:
            return False, f"家屬角色無法執行寫入工具 {tool_name}"

        # Admin always allowed (in demo)
        if role == Role.ADMIN:
            return True, ""

        # System allowed (backend-controlled)
        if role == Role.SYSTEM:
            return True, ""

        # Resident must have active_persona_id
        if role == Role.RESIDENT:
            if auth_context.active_persona_id is None:
                return False, "尚未綁定個人檔案，無法執行寫入操作"
            if target_persona_id != auth_context.active_persona_id:
                return False, "只能對自己的資料進行操作"
            return True, ""

        # Caregiver must have target in authorized set
        if role == Role.CAREGIVER:
            if target_persona_id is None:
                return False, "未指定目標使用者"
            if target_persona_id not in auth_context.authorized_persona_ids:
                return False, "無權限存取此使用者資料"
            return True, ""

        return False, "未知角色"

    @staticmethod
    def check_read_permission(
        auth_context: AuthContext,
        tool_name: str,
        target_persona_id: str | None,
    ) -> tuple[bool, str]:
        """
        Check if auth context has read permission for target persona.
        
        Returns (allowed, error_message).
        """
        role = auth_context.role

        # Admin always allowed
        if role == Role.ADMIN:
            return True, ""

        # System allowed
        if role == Role.SYSTEM:
            return True, ""

        # Resident can only read own data
        if role == Role.RESIDENT:
            if auth_context.active_persona_id is None:
                return False, "尚未綁定個人檔案，無法查詢資料"
            if target_persona_id != auth_context.active_persona_id:
                return False, "只能查詢自己的資料"
            return True, ""

        # Caregiver can read authorized personas
        if role == Role.CAREGIVER:
            if target_persona_id is None:
                return False, "未指定目標使用者"
            if target_persona_id not in auth_context.authorized_persona_ids:
                return False, "無權限查詢此使用者資料"
            return True, ""

        # Family can read authorized personas (read-only)
        if role == Role.FAMILY:
            if target_persona_id is None:
                return False, "未指定目標使用者"
            if target_persona_id not in auth_context.authorized_persona_ids:
                return False, "無權限查詢此使用者資料"
            return True, ""

        return False, "未知角色"

    @staticmethod
    def resolve_target_persona(auth_context: AuthContext) -> str | None:
        """
        Resolve target persona from auth context.
        
        For resident: uses active_persona_id
        For caregiver with single authorized: uses that one
        For others: returns None (must be specified differently)
        """
        if auth_context.role == Role.RESIDENT:
            return auth_context.active_persona_id

        # For caregiver/family with single authorized persona
        if auth_context.role in (Role.CAREGIVER, Role.FAMILY):
            if len(auth_context.authorized_persona_ids) == 1:
                return next(iter(auth_context.authorized_persona_ids))

        return None


def needs_confirmation(
    tool_name: str,
    validated_args: dict[str, Any],
) -> tuple[bool, str]:
    """
    Determine if operation needs user confirmation.
    
    Returns (needs_confirm, summary_for_user).
    """
    if tool_name == "create_care_event":
        event_type = validated_args.get("event_type")
        if event_type == EventType.MEDICATION.value or event_type == EventType.MEDICATION:
            content = validated_args.get("content", "")
            return True, f"即將記錄用藥事件：{content[:50]}"

    if tool_name == "create_reminder":
        importance = validated_args.get("importance")
        title = validated_args.get("title", "")

        if importance == Importance.HIGH.value or importance == Importance.HIGH:
            return True, f"即將建立重要提醒：{title}"

        # Check for medical keywords
        medical_keywords = ["醫院", "回診", "用藥", "藥物", "看診", "門診", "檢查", "手術"]
        if any(kw in title for kw in medical_keywords):
            return True, f"即將建立醫療相關提醒：{title}"

    return False, ""
