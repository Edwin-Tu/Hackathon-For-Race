"""
Confirmation policy and permission checking.

Confirmation is required for:
- medication events
- high importance reminders
- medical-related reminders (hospital, medication keywords)
- All modify/delete operations (when implemented)
"""

import hashlib
import json
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.repositories import CareRepository, PendingToolConfirmation
from app.tools.enums import EventType, Importance, Role
from app.tools.models import AuthContext, ToolCall


@dataclass
class PendingConfirmation:
    """
    A pending confirmation waiting for user approval.

    The complete validated ToolCall stays server-side.  The client receives
    only an opaque token and a human-readable summary.
    """

    token: str
    request_id: str
    session_id: str
    requester_id: str
    role: str
    tool_call: ToolCall
    target_persona_id: str | None
    arguments_hash: str
    created_at: float
    expires_at: float
    summary: str
    consumed: bool = False


class ConfirmationStore:
    """Pending-confirmation store with optional durable repository backing."""

    DEFAULT_TTL_SECONDS = 300  # 5 minutes

    def __init__(
        self,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        repository: CareRepository | None = None,
    ) -> None:
        self._store: dict[str, PendingConfirmation] = {}
        self._ttl_seconds = ttl_seconds
        self._repository = repository

    @staticmethod
    def _arguments_hash(validated_args: dict[str, Any]) -> str:
        canonical = json.dumps(
            validated_args,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _token_hash(token: str) -> str:
        if token.startswith("hash:"):
            return token.removeprefix("hash:")
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _to_timestamp(value: datetime) -> float:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.timestamp()

    @classmethod
    def _from_record(cls, record: PendingToolConfirmation) -> PendingConfirmation:
        return PendingConfirmation(
            token=f"hash:{record.token_hash}",
            request_id=record.request_id,
            session_id=record.session_id,
            requester_id=record.requester_id,
            role=record.role,
            tool_call=ToolCall(
                tool_call_id=record.tool_call_id,
                name=record.tool_name,
                arguments=record.arguments,
            ),
            target_persona_id=record.target_persona_id,
            arguments_hash=record.arguments_hash,
            created_at=cls._to_timestamp(record.created_at),
            expires_at=cls._to_timestamp(record.expires_at),
            summary=record.summary,
            consumed=record.consumed,
        )

    def create(
        self,
        request_id: str,
        session_id: str,
        requester_id: str,
        role: str,
        tool_call: ToolCall,
        validated_args: dict[str, Any],
        target_persona_id: str | None,
        summary: str,
    ) -> str:
        """Create one opaque token and freeze the validated ToolCall."""
        self._cleanup_expired()

        # A conversation can have only one active pending action.  Replacing an
        # older action prevents an ambiguous plain-language "確認" from
        # approving the wrong request.
        for token, pending in list(self._store.items()):
            if (
                pending.session_id == session_id
                and pending.requester_id == requester_id
                and not pending.consumed
            ):
                del self._store[token]

        token = secrets.token_urlsafe(32)
        now = time.time()
        frozen_tool_call = ToolCall(
            tool_call_id=tool_call.tool_call_id,
            name=tool_call.name,
            arguments=dict(validated_args),
        )
        pending = PendingConfirmation(
            token=token,
            request_id=request_id,
            session_id=session_id,
            requester_id=requester_id,
            role=role,
            tool_call=frozen_tool_call,
            target_persona_id=target_persona_id,
            arguments_hash=self._arguments_hash(frozen_tool_call.arguments),
            created_at=now,
            expires_at=now + self._ttl_seconds,
            summary=summary,
            consumed=False,
        )
        if self._repository is None:
            self._store[token] = pending
        else:
            self._repository.create_pending_confirmation(
                PendingToolConfirmation(
                    token_hash=self._token_hash(token),
                    request_id=request_id,
                    session_id=session_id,
                    requester_id=requester_id,
                    role=role,
                    tool_call_id=tool_call.tool_call_id,
                    tool_name=tool_call.name,
                    arguments=dict(validated_args),
                    target_persona_id=target_persona_id,
                    arguments_hash=pending.arguments_hash,
                    summary=summary,
                    created_at=datetime.fromtimestamp(now, tz=timezone.utc),
                    expires_at=datetime.fromtimestamp(
                        now + self._ttl_seconds,
                        tz=timezone.utc,
                    ),
                    consumed=False,
                )
            )
        return token

    def _validate_identity(
        self,
        pending: PendingConfirmation,
        auth_context: AuthContext,
    ) -> str:
        if pending.session_id != auth_context.session_id:
            return "確認代碼與目前工作階段不符"
        if pending.requester_id != auth_context.requester_id:
            return "確認代碼與目前使用者不符"
        if pending.role != auth_context.role.value:
            return "確認代碼與目前角色不符"
        return ""

    def get_pending(
        self,
        token: str,
        auth_context: AuthContext,
    ) -> tuple[PendingConfirmation | None, str]:
        """Resolve a token without consuming it."""
        if self._repository is None:
            self._cleanup_expired()
            pending = self._store.get(token)
        else:
            record = self._repository.get_pending_confirmation(
                token_hash=self._token_hash(token)
            )
            pending = self._from_record(record) if record is not None else None
        if pending is None:
            return None, "確認代碼無效或已過期"
        if pending.consumed:
            return None, "確認代碼已使用"
        if time.time() > pending.expires_at:
            self.consume(token, response_text="expired")
            return None, "確認代碼已過期，請重新操作"

        if self._arguments_hash(pending.tool_call.arguments) != pending.arguments_hash:
            self.consume(token, response_text="integrity_failed")
            return None, "確認資料完整性驗證失敗，請重新操作"

        identity_error = self._validate_identity(pending, auth_context)
        if identity_error:
            return None, identity_error
        return pending, ""

    def get_for_context(
        self,
        auth_context: AuthContext,
    ) -> tuple[PendingConfirmation | None, str]:
        """Find the single pending action for a trusted session/user context."""
        if self._repository is None:
            self._cleanup_expired()
            matches = [
                pending
                for pending in self._store.values()
                if not pending.consumed
                and pending.session_id == auth_context.session_id
                and pending.requester_id == auth_context.requester_id
                and pending.role == auth_context.role.value
            ]
        else:
            records = self._repository.get_pending_confirmation_for_context(
                session_id=auth_context.session_id,
                requester_id=auth_context.requester_id,
                role=auth_context.role.value,
            )
            matches = []
            now = time.time()
            for record in records:
                pending = self._from_record(record)
                if now > pending.expires_at:
                    self.consume(pending.token, response_text="expired")
                    continue
                if self._arguments_hash(pending.tool_call.arguments) != pending.arguments_hash:
                    self.consume(pending.token, response_text="integrity_failed")
                    continue
                matches.append(pending)
        if not matches:
            return None, "目前沒有待確認操作"
        if len(matches) > 1:
            return None, "目前有多筆待確認操作，請使用畫面上的確認按鈕"
        return matches[0], ""

    def consume(self, token: str, *, response_text: str = "confirmed") -> bool:
        """Remove one token so it cannot be reused."""
        if self._repository is not None:
            return self._repository.consume_pending_confirmation(
                token_hash=self._token_hash(token),
                response_text=response_text,
            )
        pending = self._store.get(token)
        if pending is None:
            return False
        pending.consumed = True
        del self._store[token]
        return True

    def cancel(
        self,
        token: str,
        auth_context: AuthContext,
    ) -> tuple[PendingConfirmation | None, str]:
        """Cancel and consume a pending action after binding checks."""
        pending, error = self.get_pending(token, auth_context)
        if pending is None:
            return None, error
        if not self.consume(token, response_text="cancelled"):
            return None, "確認代碼已使用"
        return pending, ""

    def _cleanup_expired(self) -> None:
        now = time.time()
        expired = [key for key, value in self._store.items() if now > value.expires_at]
        for key in expired:
            del self._store[key]


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
