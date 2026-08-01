"""
Tool Gateway: central orchestrator for tool execution.

Processing order:
1. Check Tool Registry
2. Check role permission
3. Validate persona scope
4. Pydantic schema validation
5. Inject target_persona_id from AuthContext
6. Check risk and confirmation policy
7. Check idempotency
8. Execute handler with timeout
9. Store ToolResult
10. Write minimal audit

Fail-closed on:
- Unknown tools
- Missing permission info
- Any unexpected exception
- Timeout
"""

import concurrent.futures
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from app.tools.audit import InMemoryAuditStore, extract_argument_names
from app.tools.enums import RiskLevel, Role, ToolStatus
from app.repositories import CareRepository, InMemoryCareRepository
from app.tools.handlers import ToolHandlers
from app.tools.idempotency import InMemoryIdempotencyStore
from app.tools.models import AuthContext, ToolCall, ToolResult
from app.tools.policy import ConfirmationStore, PermissionPolicy, needs_confirmation
from app.tools.registry import ToolRegistry, create_default_registry

logger = logging.getLogger(__name__)

# Maximum tools per user turn
MAX_TOOLS_PER_TURN = 2

# Default tool timeout in seconds
DEFAULT_TOOL_TIMEOUT_SECONDS = 30



class ToolGateway:
    """
    Gateway for validating and executing tool calls.
    
    Claude only proposes toolUse.
    Gateway decides: tool exists, args valid, role allowed,
    persona scope ok, confirmation needed, idempotency check.
    
    Model MUST NOT execute SQL directly.
    Model MUST NOT determine trusted persona_id.
    """

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        repository: CareRepository | None = None,
        audit_store: InMemoryAuditStore | None = None,
        idempotency_store: InMemoryIdempotencyStore | None = None,
        confirmation_store: ConfirmationStore | None = None,
    ) -> None:
        self._registry = registry or create_default_registry()
        self._repository = repository or InMemoryCareRepository()
        self._audit = audit_store or InMemoryAuditStore()
        self._idempotency = idempotency_store or InMemoryIdempotencyStore()
        self._confirmation = confirmation_store or ConfirmationStore()
        self._handlers = ToolHandlers(self._repository)
        self._turn_tool_counts: dict[str, int] = {}

        # Wire up handlers in registry
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Connect handlers to registry tools."""
        tool = self._registry.get("create_care_event")
        if tool:
            tool.handler = self._handlers.handle_create_care_event

        tool = self._registry.get("create_reminder")
        if tool:
            tool.handler = self._handlers.handle_create_reminder

        tool = self._registry.get("get_user_schedule")
        if tool:
            tool.handler = self._handlers.handle_get_user_schedule


    def _make_result(
        self,
        tool_call: ToolCall,
        status: ToolStatus,
        success: bool,
        message: str,
        started_at: datetime,
        **kwargs: Any,
    ) -> ToolResult:
        """Create a ToolResult with standard fields."""
        return ToolResult(
            tool_call_id=tool_call.tool_call_id,
            tool_name=tool_call.name,
            status=status,
            success=success,
            message=message,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            **kwargs,
        )

    def _check_turn_limit(self, request_id: str) -> bool:
        """Check if turn has exceeded tool limit."""
        count = self._turn_tool_counts.get(request_id, 0)
        return count < MAX_TOOLS_PER_TURN

    def _increment_turn_count(self, request_id: str) -> None:
        """Increment tool count for this turn."""
        self._turn_tool_counts[request_id] = (
            self._turn_tool_counts.get(request_id, 0) + 1
        )

    def reset_turn_count(self, request_id: str) -> None:
        """Reset turn count (call at start of new turn)."""
        self._turn_tool_counts.pop(request_id, None)

    def get_bedrock_tool_config(self, auth_context: AuthContext) -> list[dict]:
        """Get Bedrock tool configuration filtered by role."""
        return self._registry.get_bedrock_tool_config(auth_context)


    def preflight(
        self,
        tool_call: ToolCall,
        auth_context: AuthContext,
    ) -> ToolResult:
        """
        Validate tool call without executing.
        
        Returns validated ToolResult or error.
        """
        started_at = datetime.now(timezone.utc)
        start_time = time.time()
        target_persona_id: str | None = None

        try:
            # 1. Check turn limit
            if not self._check_turn_limit(auth_context.request_id):
                return self._deny(
                    tool_call, started_at, "TURN_LIMIT_EXCEEDED",
                    "單次對話最多執行兩個工具", auth_context, None,
                )

            # 2. Check tool exists
            tool_def = self._registry.get(tool_call.name)
            if tool_def is None:
                return self._deny(
                    tool_call, started_at, "UNKNOWN_TOOL",
                    f"未知的工具：{tool_call.name}", auth_context, None,
                )

            # 3. Check role allowed
            if auth_context.role not in tool_def.allowed_roles:
                return self._deny(
                    tool_call, started_at, "ROLE_NOT_ALLOWED",
                    f"您的角色無法使用此工具", auth_context, None,
                )

            # 4. Validate arguments with Pydantic
            try:
                validated = tool_def.argument_model(**tool_call.arguments)
                validated_args = validated.model_dump()
            except ValidationError as e:
                errors = e.errors()
                # Check for extra fields (persona_id injection attempt)
                extra_fields = [
                    err for err in errors
                    if err.get("type") == "extra_forbidden"
                ]
                if extra_fields:
                    field_names = [str(err.get("loc", ["unknown"])[0]) for err in extra_fields]
                    return self._deny(
                        tool_call, started_at, "FORBIDDEN_FIELD",
                        f"不允許的欄位：{', '.join(field_names)}", auth_context, None,
                    )
                # Other validation errors
                msg = "; ".join(f"{e['loc']}: {e['msg']}" for e in errors[:3])
                return self._deny(
                    tool_call, started_at, "VALIDATION_ERROR",
                    f"參數驗證失敗：{msg}", auth_context, None,
                )

            # 5. Resolve target persona
            target_persona_id = PermissionPolicy.resolve_target_persona(auth_context)

            # 6. Check permission
            if tool_def.is_write:
                allowed, err_msg = PermissionPolicy.check_write_permission(
                    auth_context, tool_call.name, target_persona_id
                )
            else:
                allowed, err_msg = PermissionPolicy.check_read_permission(
                    auth_context, tool_call.name, target_persona_id
                )

            if not allowed:
                return self._deny(
                    tool_call, started_at, "PERMISSION_DENIED",
                    err_msg, auth_context, target_persona_id,
                )

            # 7. Check idempotency key for writes
            if tool_def.is_write:
                idem_key = validated_args.get("idempotency_key")
                if not idem_key:
                    return self._deny(
                        tool_call, started_at, "MISSING_IDEMPOTENCY_KEY",
                        "寫入操作必須提供 idempotency_key", auth_context, target_persona_id,
                    )

            # Preflight passed
            duration_ms = int((time.time() - start_time) * 1000)
            self._audit.log(
                auth_context=auth_context,
                tool_name=tool_call.name,
                argument_names=extract_argument_names(tool_call.arguments),
                target_persona_id=target_persona_id,
                decision="allow",
                status=ToolStatus.VALIDATED,
                risk_level=tool_def.risk_level,
                duration_ms=duration_ms,
            )

            return self._make_result(
                tool_call, ToolStatus.VALIDATED, True,
                "驗證通過", started_at,
                metadata={"target_persona_id": target_persona_id},
            )

        except Exception as e:
            logger.exception("Unexpected error in preflight")
            return self._deny(
                tool_call, started_at, "PREFLIGHT_ERROR",
                "系統錯誤，請稍後重試", auth_context, target_persona_id,
            )


    def execute(
        self,
        tool_call: ToolCall,
        auth_context: AuthContext,
    ) -> ToolResult:
        """
        Execute tool call with full validation.
        
        Processing:
        1. Preflight validation
        2. Confirmation check (if needed)
        3. Idempotency check
        4. Handler execution with timeout
        5. Audit logging
        """
        started_at = datetime.now(timezone.utc)
        start_time = time.time()

        # Run preflight first
        preflight_result = self.preflight(tool_call, auth_context)
        if not preflight_result.success:
            return preflight_result

        target_persona_id = preflight_result.metadata.get("target_persona_id")
        tool_def = self._registry.get(tool_call.name)
        assert tool_def is not None  # Already validated in preflight

        try:
            # Validate args again (belt and suspenders)
            validated = tool_def.argument_model(**tool_call.arguments)
            validated_args = validated.model_dump()

            # Check confirmation if needed
            requires_conf, conf_summary = needs_confirmation(
                tool_call.name, validated_args
            )

            if requires_conf and not tool_call.confirmation_token:
                # Need confirmation - create token and store complete ToolCall
                token = self._confirmation.create(
                    request_id=auth_context.request_id,
                    session_id=auth_context.session_id,
                    requester_id=auth_context.requester_id,
                    role=auth_context.role.value,
                    tool_call=tool_call,
                    validated_args=validated_args,
                    target_persona_id=target_persona_id,
                    summary=conf_summary,
                )

                duration_ms = int((time.time() - start_time) * 1000)
                self._audit.log(
                    auth_context=auth_context,
                    tool_name=tool_call.name,
                    argument_names=extract_argument_names(tool_call.arguments),
                    target_persona_id=target_persona_id,
                    decision="confirm",
                    status=ToolStatus.AWAITING_CONFIRMATION,
                    risk_level=tool_def.risk_level,
                    requires_confirmation=True,
                    duration_ms=duration_ms,
                )

                return self._make_result(
                    tool_call, ToolStatus.AWAITING_CONFIRMATION, False,
                    conf_summary, started_at,
                    requires_confirmation=True,
                    confirmation_summary=conf_summary,
                    confirmation_token=token,
                )

            # Check idempotency for writes
            if tool_def.is_write:
                idem_key = validated_args.get("idempotency_key")
                existing = self._idempotency.get(
                    auth_context.session_id,
                    tool_call.name,
                    target_persona_id,
                    idem_key,
                )
                if existing is not None:
                    # Return original result with replay flag and updated tool_call_id
                    return ToolResult(
                        tool_call_id=tool_call.tool_call_id,
                        tool_name=existing.tool_name,
                        status=existing.status,
                        success=existing.success,
                        message=existing.message,
                        record_id=existing.record_id,
                        error_code=existing.error_code,
                        requires_confirmation=False,
                        idempotency_replayed=True,
                        started_at=existing.started_at,
                        finished_at=existing.finished_at,
                        metadata=existing.metadata,
                    )

            # Increment turn count
            self._increment_turn_count(auth_context.request_id)

            # Execute handler with timeout
            timeout_seconds = tool_def.max_timeout_seconds or DEFAULT_TOOL_TIMEOUT_SECONDS
            try:
                result_data = self._execute_with_timeout(
                    handler=tool_def.handler,
                    validated_args=validated_args,
                    target_persona_id=target_persona_id,
                    requester_id=auth_context.requester_id,
                    timeout_seconds=timeout_seconds,
                )
            except TimeoutError:
                logger.warning("Tool execution timed out: %s", tool_call.name)
                return self._deny(
                    tool_call, started_at, "TOOL_TIMEOUT",
                    "工具執行逾時，請稍後重試", auth_context, target_persona_id,
                )
            except Exception as e:
                logger.exception("Handler execution failed")
                return self._deny(
                    tool_call, started_at, "TOOL_EXECUTION_ERROR",
                    "工具執行失敗，請稍後重試", auth_context, target_persona_id,
                )

            record_id = result_data.get("record_id")
            message = result_data.get("message", "操作完成")

            # Create success result
            result = self._make_result(
                tool_call, ToolStatus.SUCCEEDED, True,
                message, started_at,
                record_id=record_id,
                metadata={
                    "target_persona_id": target_persona_id,
                    **{k: v for k, v in result_data.items() if k not in ("record_id", "message")},
                },
            )

            # Store for idempotency
            if tool_def.is_write:
                idem_key = validated_args.get("idempotency_key")
                self._idempotency.store(
                    auth_context.session_id,
                    tool_call.name,
                    target_persona_id,
                    idem_key,
                    result,
                )

            # Audit success
            duration_ms = int((time.time() - start_time) * 1000)
            self._audit.log(
                auth_context=auth_context,
                tool_name=tool_call.name,
                argument_names=extract_argument_names(tool_call.arguments),
                target_persona_id=target_persona_id,
                decision="allow",
                status=ToolStatus.SUCCEEDED,
                risk_level=tool_def.risk_level,
                record_id=record_id,
                duration_ms=duration_ms,
            )

            return result

        except Exception as e:
            logger.exception("Unexpected error in execute")
            return self._deny(
                tool_call, started_at, "TOOL_EXECUTION_ERROR",
                "系統錯誤，請稍後重試", auth_context, target_persona_id,
            )

    def _execute_with_timeout(
        self,
        handler: Any,
        validated_args: dict[str, Any],
        target_persona_id: str,
        requester_id: str,
        timeout_seconds: int,
    ) -> dict[str, Any]:
        """
        Execute handler with timeout.
        
        Raises TimeoutError if execution exceeds timeout.
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                handler,
                validated_args=validated_args,
                target_persona_id=target_persona_id,
                requester_id=requester_id,
            )
            try:
                return future.result(timeout=timeout_seconds)
            except concurrent.futures.TimeoutError:
                raise TimeoutError(f"Handler execution exceeded {timeout_seconds}s")


    def get_pending_confirmation(
        self,
        auth_context: AuthContext,
    ) -> tuple[str | None, str | None, str | None]:
        """Return only token/summary for the current trusted context."""
        pending, error = self._confirmation.get_for_context(auth_context)
        if pending is None:
            return None, None, error
        return pending.token, pending.summary, None

    def cancel_confirmation(
        self,
        confirmation_token: str,
        auth_context: AuthContext,
    ) -> ToolResult:
        """Cancel one server-side pending ToolCall without invoking its handler."""
        started_at = datetime.now(timezone.utc)
        pending, error = self._confirmation.cancel(confirmation_token, auth_context)
        if pending is None:
            placeholder_call = ToolCall(
                tool_call_id=f"cancel-denied-{uuid.uuid4()}",
                name="unknown",
                arguments={},
            )
            return self._deny(
                placeholder_call,
                started_at,
                "INVALID_CONFIRMATION",
                error,
                auth_context,
                None,
            )

        return self._make_result(
            pending.tool_call,
            ToolStatus.CANCELLED,
            False,
            "已取消待確認操作，未執行任何工具。",
            started_at,
            metadata={"target_persona_id": pending.target_persona_id},
        )

    def confirm_and_execute(
        self,
        confirmation_token: str,
        auth_context: AuthContext,
    ) -> ToolResult:
        """
        Execute a confirmed tool call.
        
        The confirmation_token is validated against server-stored pending confirmation.
        Arguments are retrieved from server storage, NOT accepted from client.
        Token is single-use and expires after 5 minutes.
        """
        started_at = datetime.now(timezone.utc)

        # Get pending confirmation from server storage
        pending, err_msg = self._confirmation.get_pending(
            confirmation_token, auth_context
        )

        if pending is None:
            # Create a placeholder tool_call for denial logging
            placeholder_call = ToolCall(
                tool_call_id=f"denied-{uuid.uuid4()}",
                name="unknown",
                arguments={},
            )
            return self._deny(
                placeholder_call, started_at, "INVALID_CONFIRMATION",
                err_msg, auth_context, None,
            )

        # Use the stored ToolCall from server - client cannot modify arguments
        tool_call = pending.tool_call
        target_persona_id = pending.target_persona_id

        # Consume the token (single-use)
        self._confirmation.consume(confirmation_token)

        # Now execute the stored tool call
        tool_def = self._registry.get(tool_call.name)
        if tool_def is None:
            return self._deny(
                tool_call, started_at, "UNKNOWN_TOOL",
                f"未知的工具：{tool_call.name}", auth_context, target_persona_id,
            )

        try:
            # Re-validate permission (auth context may have changed)
            if tool_def.is_write:
                allowed, perm_err = PermissionPolicy.check_write_permission(
                    auth_context, tool_call.name, target_persona_id
                )
            else:
                allowed, perm_err = PermissionPolicy.check_read_permission(
                    auth_context, tool_call.name, target_persona_id
                )

            if not allowed:
                return self._deny(
                    tool_call, started_at, "PERMISSION_DENIED",
                    perm_err, auth_context, target_persona_id,
                )

            # Validate arguments
            validated = tool_def.argument_model(**tool_call.arguments)
            validated_args = validated.model_dump()

            # Check idempotency for writes
            if tool_def.is_write:
                idem_key = validated_args.get("idempotency_key")
                existing = self._idempotency.get(
                    auth_context.session_id,
                    tool_call.name,
                    target_persona_id,
                    idem_key,
                )
                if existing is not None:
                    return ToolResult(
                        tool_call_id=tool_call.tool_call_id,
                        tool_name=existing.tool_name,
                        status=existing.status,
                        success=existing.success,
                        message=existing.message,
                        record_id=existing.record_id,
                        error_code=existing.error_code,
                        requires_confirmation=False,
                        idempotency_replayed=True,
                        started_at=existing.started_at,
                        finished_at=existing.finished_at,
                        metadata=existing.metadata,
                    )

            # Execute handler with timeout
            timeout_seconds = tool_def.max_timeout_seconds or DEFAULT_TOOL_TIMEOUT_SECONDS
            start_time = time.time()

            try:
                result_data = self._execute_with_timeout(
                    handler=tool_def.handler,
                    validated_args=validated_args,
                    target_persona_id=target_persona_id,
                    requester_id=auth_context.requester_id,
                    timeout_seconds=timeout_seconds,
                )
            except TimeoutError:
                logger.warning("Tool execution timed out: %s", tool_call.name)
                return self._deny(
                    tool_call, started_at, "TOOL_TIMEOUT",
                    "工具執行逾時，請稍後重試", auth_context, target_persona_id,
                )
            except Exception:
                logger.exception("Handler execution failed in confirm_and_execute")
                return self._deny(
                    tool_call, started_at, "TOOL_EXECUTION_ERROR",
                    "工具執行失敗，請稍後重試", auth_context, target_persona_id,
                )

            record_id = result_data.get("record_id")
            message = result_data.get("message", "操作完成")

            result = self._make_result(
                tool_call, ToolStatus.SUCCEEDED, True,
                message, started_at,
                record_id=record_id,
                metadata={
                    "target_persona_id": target_persona_id,
                    **{k: v for k, v in result_data.items() if k not in ("record_id", "message")},
                },
            )

            # Store for idempotency
            if tool_def.is_write:
                idem_key = validated_args.get("idempotency_key")
                self._idempotency.store(
                    auth_context.session_id,
                    tool_call.name,
                    target_persona_id,
                    idem_key,
                    result,
                )

            # Audit success
            duration_ms = int((time.time() - start_time) * 1000)
            self._audit.log(
                auth_context=auth_context,
                tool_name=tool_call.name,
                argument_names=extract_argument_names(tool_call.arguments),
                target_persona_id=target_persona_id,
                decision="allow",
                status=ToolStatus.SUCCEEDED,
                risk_level=tool_def.risk_level,
                record_id=record_id,
                duration_ms=duration_ms,
            )

            return result

        except Exception:
            logger.exception("Unexpected error in confirm_and_execute")
            return self._deny(
                tool_call, started_at, "TOOL_EXECUTION_ERROR",
                "系統錯誤，請稍後重試", auth_context, target_persona_id,
            )

    def _deny(
        self,
        tool_call: ToolCall,
        started_at: datetime,
        error_code: str,
        message: str,
        auth_context: AuthContext,
        target_persona_id: str | None,
    ) -> ToolResult:
        """Create a denied ToolResult and log audit."""
        tool_def = self._registry.get(tool_call.name)
        risk_level = tool_def.risk_level if tool_def else RiskLevel.LOW

        self._audit.log(
            auth_context=auth_context,
            tool_name=tool_call.name,
            argument_names=extract_argument_names(tool_call.arguments),
            target_persona_id=target_persona_id,
            decision="deny",
            status=ToolStatus.DENIED,
            risk_level=risk_level,
            error_code=error_code,
        )

        return self._make_result(
            tool_call, ToolStatus.DENIED, False,
            message, started_at,
            error_code=error_code,
        )

    # Expose stores for testing
    @property
    def audit_store(self) -> InMemoryAuditStore:
        return self._audit

    @property
    def repository(self) -> CareRepository:
        return self._repository

    @property
    def registry(self) -> ToolRegistry:
        return self._registry
