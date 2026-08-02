"""Agent service: orchestrates Bedrock calls with a guarded tool loop."""

import logging
import uuid
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.config import settings
from app.models import (
    ActionStatus,
    ChatRequest,
    ChatResponse,
    ConfirmationDecision,
    ConfirmationRequest,
    InputGuardEvidence,
    ToolEvent,
    UsageInfo,
)
from app.providers.base import BaseLLMProvider
from app.repositories import CareRepository, SessionScopeError
from app.security import AgentInputGuard
from app.services.intent_router import IntentDecision, RequestedAction, classify_intent
from app.skills import (
    SkillContext,
    SkillRegistry,
    SkillRoutingResult,
    create_default_skill_registry,
)
from app.tools import (
    AuthContext,
    DemoAuthContextFactory,
    ToolCall,
    ToolGateway,
    ToolResult,
    ToolStatus,
)

logger = logging.getLogger(__name__)

TAIPEI_TZ = ZoneInfo("Asia/Taipei")
WRITE_TOOLS = {"create_care_event", "create_reminder"}
READ_TOOLS = {"get_user_schedule"}
SUCCESS_CLAIMS = (
    "已記錄",
    "已經記錄",
    "已建立",
    "已保存",
    "已完成",
    "已新增",
)
CONFIRMATION_PHRASES = {
    "確認",
    "確定",
    "同意",
    "好",
    "好的",
    "可以",
    "是",
    "是的",
    "執行",
    "確認執行",
    "確認建立",
    "沒問題",
}
CANCELLATION_PHRASES = {
    "取消",
    "不要",
    "不用了",
    "先不要",
    "否",
    "取消操作",
    "不要執行",
}

SYSTEM_PROMPT_TEMPLATE = """你是一個智慧長照生活協助系統。請嚴格遵守以下規則：

可信任時間：
- 目前時間：{current_datetime}
- 目前日期：{current_date}
- 系統時區：Asia/Taipei
- 所有「今天、明天、剛剛、下午、晚上」等相對時間，都必須以上述伺服器時間為基準，不得自行猜測其他年份或日期。
- 若使用者只提供模糊時段而沒有明確時刻，應詢問缺少的資訊，不得自行填入固定時間。

全域安全規則：
- 你的定位是生活協助，不提供醫療診斷、處方或藥物調整建議。
- 工具請求只是提案，不代表操作已完成。
- 尚未取得真實 ToolResult 前，不得宣稱已記錄、已建立、已保存或已通知。
- 只有寫入工具回傳 success=true、status=succeeded 且 record_id 非空時，才能告知使用者寫入完成。
- 不得要求或自行產生 persona_id、resident_id、requester_id、角色或授權清單。
- 不得要求未提供的工具，也不得嘗試 SQL、Shell、任意檔案或任意 HTTP 操作。
- 工具需要確認時，只說明需確認的內容，不得提及確認代碼。
- 工具失敗或遭拒絕時，應說明尚未完成，不得捏造 record_id。

本回合啟用技能：
{skill_instructions}
"""

MAX_CONVERSE_ROUNDS = 3
MAX_TOOLS_PER_TURN = 2


class AgentService:
    """Service that handles chat logic with intent-constrained tool use."""

    def __init__(
        self,
        provider: BaseLLMProvider,
        gateway: ToolGateway | None = None,
        skill_registry: SkillRegistry | None = None,
        input_guard: AgentInputGuard | None = None,
        repository: CareRepository | None = None,
    ) -> None:
        self._provider = provider
        self._gateway = gateway or ToolGateway()
        self._skill_registry = skill_registry or create_default_skill_registry()
        self._input_guard = input_guard or AgentInputGuard(
            enabled=settings.INPUT_GUARD_ENABLED,
            fail_closed=settings.INPUT_GUARD_FAIL_CLOSED,
        )
        self._repository = repository or self._gateway.repository

    def _create_demo_auth_context(
        self,
        session_id: str,
        request_id: str,
    ) -> AuthContext:
        """Create development-only auth context."""
        return DemoAuthContextFactory.create_resident(
            requester_id=settings.DEMO_USER_ID,
            persona_id=settings.DEMO_PERSONA_ID,
            session_id=session_id,
            request_id=request_id,
        )

    def _build_system_prompt(self, skills: SkillRoutingResult) -> str:
        """Build a protected prompt from trusted time and selected skills."""
        now = datetime.now(TAIPEI_TZ)
        return SYSTEM_PROMPT_TEMPLATE.format(
            current_datetime=now.isoformat(timespec="seconds"),
            current_date=now.date().isoformat(),
            skill_instructions=skills.to_prompt_block(),
        )

    @staticmethod
    def _conversation_persona_id(auth_context: AuthContext) -> str:
        if auth_context.active_persona_id:
            return auth_context.active_persona_id
        if len(auth_context.authorized_persona_ids) == 1:
            return next(iter(auth_context.authorized_persona_ids))
        raise SessionScopeError(
            "conversation requires exactly one trusted persona scope"
        )

    def _load_conversation_history(
        self,
        auth_context: AuthContext,
    ) -> list[dict[str, Any]]:
        if not settings.CONVERSATION_HISTORY_ENABLED:
            return []
        persona_id = self._conversation_persona_id(auth_context)
        self._repository.ensure_conversation_session(
            session_id=auth_context.session_id,
            user_id=auth_context.requester_id,
            persona_id=persona_id,
        )
        history = self._repository.list_recent_conversation_messages(
            session_id=auth_context.session_id,
            user_id=auth_context.requester_id,
            persona_id=persona_id,
            max_messages=max(0, settings.CONVERSATION_HISTORY_MAX_MESSAGES),
            max_chars=max(1, settings.CONVERSATION_HISTORY_MAX_CHARS),
        )
        return [
            {"role": message.role, "content": message.content}
            for message in history
            if message.content.strip()
        ]

    def _persist_conversation_turn(
        self,
        *,
        auth_context: AuthContext,
        user_message: str,
        assistant_message: str,
        input_type: str = "text",
    ) -> None:
        if not settings.CONVERSATION_HISTORY_ENABLED:
            return
        if not user_message.strip() and not assistant_message.strip():
            return
        persona_id = self._conversation_persona_id(auth_context)
        try:
            self._repository.append_conversation_turn(
                session_id=auth_context.session_id,
                user_id=auth_context.requester_id,
                persona_id=persona_id,
                request_id=auth_context.request_id,
                user_message=user_message,
                assistant_message=assistant_message,
                input_type=input_type,
            )
        except Exception:
            # A completed tool operation remains completed even if conversation
            # journaling fails. The error is logged without message contents.
            logger.exception(
                "Conversation turn persistence failed request_id=%s session_id=%s",
                auth_context.request_id,
                auth_context.session_id,
            )

    @staticmethod
    def _conversation_error_response(
        *,
        session_id: str,
        input_guard: InputGuardEvidence,
        error_type: str,
        message: str,
    ) -> ChatResponse:
        return ChatResponse(
            success=False,
            reply=message,
            model="",
            session_id=session_id,
            usage=UsageInfo(),
            error_type=error_type,
            error_message=message,
            operation_completed=False,
            action_status=ActionStatus.DENIED,
            tool_events=[],
            input_guard=input_guard,
        )

    def _build_tool_configs(
        self,
        auth_context: AuthContext,
        intent: IntentDecision,
        skills: SkillRoutingResult,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """Build initial and follow-up Bedrock toolConfig objects.

        Only the expected tool is exposed for an explicit intent. The first
        round may force that tool when the utterance contains enough time
        information. Follow-up rounds remove toolChoice so the model can end
        the turn after receiving toolResult.
        """
        if intent.expected_tool is None or skills.blocked:
            return None, None
        if intent.expected_tool not in skills.allowed_tools:
            logger.warning(
                "Skill/tool mismatch: expected=%s allowed=%s",
                intent.expected_tool,
                skills.allowed_tools,
            )
            return None, None

        all_specs = self._gateway.get_bedrock_tool_config(auth_context)
        filtered = [
            item
            for item in all_specs
            if item.get("toolSpec", {}).get("name") == intent.expected_tool
            and item.get("toolSpec", {}).get("name") in skills.allowed_tools
        ]
        if not filtered:
            return None, None

        initial: dict[str, Any] = {"tools": filtered}
        if intent.force_tool:
            initial["toolChoice"] = {
                "tool": {"name": intent.expected_tool}
            }
        follow_up: dict[str, Any] = {"tools": filtered}
        return initial, follow_up

    def _make_tool_event(self, tool_result: ToolResult) -> ToolEvent:
        """Create a safe API event from a gateway result."""
        return ToolEvent(
            tool_call_id=tool_result.tool_call_id,
            tool_name=tool_result.tool_name,
            status=tool_result.status.value,
            success=tool_result.success,
            record_id=tool_result.record_id,
            error_code=tool_result.error_code,
            idempotency_replayed=tool_result.idempotency_replayed,
        )

    @staticmethod
    def _is_completed_write(event: ToolEvent) -> bool:
        return (
            event.tool_name in WRITE_TOOLS
            and event.status == ToolStatus.SUCCEEDED.value
            and event.success is True
            and bool(event.record_id)
        )

    @staticmethod
    def _is_completed_query(event: ToolEvent) -> bool:
        return (
            event.tool_name in READ_TOOLS
            and event.status == ToolStatus.SUCCEEDED.value
            and event.success is True
        )

    def _derive_action_status(
        self,
        intent: IntentDecision,
        tool_events: list[ToolEvent],
    ) -> tuple[bool, ActionStatus]:
        """Derive state strictly from backend tool evidence."""
        write_completed = any(self._is_completed_write(e) for e in tool_events)
        query_completed = any(self._is_completed_query(e) for e in tool_events)

        if write_completed:
            return True, ActionStatus.COMPLETED
        if query_completed:
            return False, ActionStatus.QUERY_COMPLETED
        if any(e.status == ToolStatus.DENIED.value for e in tool_events):
            return False, ActionStatus.DENIED
        if tool_events:
            return False, ActionStatus.FAILED
        if intent.expected_tool is not None:
            return False, ActionStatus.CLARIFICATION_REQUIRED
        return False, ActionStatus.NO_ACTION

    def _guard_final_reply(
        self,
        reply: str,
        operation_completed: bool,
        action_status: ActionStatus,
    ) -> str:
        """Prevent natural-language success claims unsupported by evidence."""
        if operation_completed:
            return reply

        if any(claim in reply for claim in SUCCESS_CLAIMS):
            if action_status == ActionStatus.CLARIFICATION_REQUIRED:
                return "這項操作尚未完成，請補充缺少的日期或時間資訊。"
            if action_status == ActionStatus.DENIED:
                return "這項操作未獲授權，因此尚未完成。"
            if action_status == ActionStatus.FAILED:
                return "這項操作尚未完成，請稍後再試。"
        return reply

    @staticmethod
    def _parse_confirmation_decision(message: str) -> ConfirmationDecision | None:
        """Recognize a short, explicit confirmation/cancellation utterance."""
        normalized = "".join(
            ch for ch in message.strip().lower()
            if ch not in " \t\r\n，。！？!?、,."
        )
        if normalized in CONFIRMATION_PHRASES:
            return ConfirmationDecision.CONFIRM
        if normalized in CANCELLATION_PHRASES:
            return ConfirmationDecision.CANCEL
        return None

    async def confirm(self, request: ConfirmationRequest) -> ChatResponse:
        """Resolve an explicit confirmation endpoint without calling Bedrock."""
        request_id = str(uuid.uuid4())
        auth_context = self._create_demo_auth_context(request.session_id, request_id)
        if request.decision == ConfirmationDecision.CANCEL:
            return await self._handle_cancellation(
                request.confirmation_token,
                auth_context,
                request.session_id,
            )
        return await self._handle_confirmation(
            request.confirmation_token,
            auth_context,
            request.session_id,
        )

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request with constrained Bedrock tool use."""
        session_id = request.session_id or str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        auth_context = self._create_demo_auth_context(session_id, request_id)

        if request.confirmation_token:
            return await self._handle_confirmation(
                request.confirmation_token,
                auth_context,
                session_id,
            )

        guard_outcome = self._input_guard.inspect(
            text=request.message,
            auth_context=auth_context,
        )
        logger.info(
            "Input Guard request_id=%s action=%s allowed=%s risk=%s category=%s",
            request_id,
            guard_outcome.evidence.action,
            guard_outcome.allowed,
            guard_outcome.evidence.overall_risk_score,
            guard_outcome.evidence.primary_category,
        )
        if not guard_outcome.allowed:
            return ChatResponse(
                success=False,
                reply=(
                    "我無法協助處理這項請求。"
                    + (
                        guard_outcome.safe_response
                        or "這項請求未通過安全檢查，因此尚未處理。"
                    )
                ),
                model="",
                session_id=session_id,
                usage=UsageInfo(),
                error_type="SECURITY_POLICY_BLOCK",
                error_message="請求在呼叫模型前被 Input Guard 阻擋",
                operation_completed=False,
                action_status=ActionStatus.DENIED,
                tool_events=[],
                input_guard=guard_outcome.evidence,
            )

        guarded_message = guard_outcome.sanitized_text or request.message

        # Plain-language or voice confirmation resumes the one pending action
        # bound to this trusted session/user.  This path never calls Bedrock.
        decision = self._parse_confirmation_decision(guarded_message)
        if decision is not None:
            pending_token, _, pending_error = self._gateway.get_pending_confirmation(
                auth_context
            )
            if pending_token is None:
                return ChatResponse(
                    success=False,
                    reply=pending_error or "目前沒有待確認操作。",
                    model="",
                    session_id=session_id,
                    usage=UsageInfo(),
                    error_type="NO_PENDING_CONFIRMATION",
                    error_message=pending_error or "目前沒有待確認操作",
                    operation_completed=False,
                    action_status=ActionStatus.NO_ACTION,
                    tool_events=[],
                    input_guard=guard_outcome.evidence,
                )
            if decision == ConfirmationDecision.CANCEL:
                return await self._handle_cancellation(
                    pending_token,
                    auth_context,
                    session_id,
                    input_guard=guard_outcome.evidence,
                    user_message=guarded_message,
                    input_type=request.input_type,
                )
            return await self._handle_confirmation(
                pending_token,
                auth_context,
                session_id,
                input_guard=guard_outcome.evidence,
                user_message=guarded_message,
                input_type=request.input_type,
            )

        try:
            conversation_history = self._load_conversation_history(auth_context)
        except SessionScopeError as exc:
            logger.warning(
                "Conversation scope denied request_id=%s session_id=%s",
                request_id,
                session_id,
            )
            return self._conversation_error_response(
                session_id=session_id,
                input_guard=guard_outcome.evidence,
                error_type="SESSION_SCOPE_DENIED",
                message=str(exc),
            )
        except Exception:
            logger.exception(
                "Conversation history load failed request_id=%s session_id=%s",
                request_id,
                session_id,
            )
            return self._conversation_error_response(
                session_id=session_id,
                input_guard=guard_outcome.evidence,
                error_type="CONVERSATION_STORAGE_ERROR",
                message="目前無法載入安全對話上下文，請稍後再試。",
            )

        self._gateway.reset_turn_count(request_id)
        intent = classify_intent(guarded_message)
        skills = self._skill_registry.route(
            SkillContext(
                message=guarded_message,
                action=intent.action.value,
                user_role=auth_context.role.value,
            )
        )
        logger.info(
            "Enabled skills request_id=%s skills=%s allowed_tools=%s blocked=%s",
            request_id,
            skills.selected_skills,
            skills.allowed_tools,
            skills.blocked,
        )

        if skills.blocked:
            return ChatResponse(
                success=False,
                reply=skills.safe_response or "這項請求因安全限制無法處理。",
                model="",
                session_id=session_id,
                usage=UsageInfo(),
                error_type="SECURITY_POLICY_BLOCK",
                error_message="請求被安全技能阻擋",
                operation_completed=False,
                action_status=ActionStatus.DENIED,
                tool_events=[],
                input_guard=guard_outcome.evidence,
            )

        initial_tool_config, follow_up_tool_config = self._build_tool_configs(
            auth_context, intent, skills
        )

        messages: list[dict[str, Any]] = [
            *conversation_history,
            {"role": "user", "content": guarded_message},
        ]
        total_usage = UsageInfo()
        tools_executed = 0
        tool_events: list[ToolEvent] = []
        system_prompt = self._build_system_prompt(skills)
        last_model = ""

        for round_num in range(MAX_CONVERSE_ROUNDS):
            tool_config = (
                initial_tool_config if round_num == 0 else follow_up_tool_config
            )
            result = await self._provider.chat(
                messages=messages,
                system_prompt=system_prompt,
                tool_config=tool_config,
            )
            last_model = result.model

            if not result.success:
                return ChatResponse(
                    success=False,
                    reply="",
                    model=result.model,
                    session_id=session_id,
                    usage=total_usage,
                    error_type=result.error_type,
                    error_message=result.error_message,
                    operation_completed=False,
                    action_status=ActionStatus.FAILED,
                    tool_events=tool_events,
                    input_guard=guard_outcome.evidence,
                )

            total_usage = UsageInfo(
                input_tokens=total_usage.input_tokens + result.usage.input_tokens,
                output_tokens=total_usage.output_tokens + result.usage.output_tokens,
                total_tokens=total_usage.total_tokens + result.usage.total_tokens,
            )

            if result.stop_reason == "end_turn" or not result.tool_use_blocks:
                operation_completed, action_status = self._derive_action_status(
                    intent, tool_events
                )
                reply = self._guard_final_reply(
                    result.text,
                    operation_completed,
                    action_status,
                )
                self._persist_conversation_turn(
                    auth_context=auth_context,
                    user_message=guarded_message,
                    assistant_message=reply,
                    input_type=request.input_type,
                )
                return ChatResponse(
                    success=True,
                    reply=reply,
                    model=result.model,
                    session_id=session_id,
                    usage=total_usage,
                    operation_completed=operation_completed,
                    action_status=action_status,
                    tool_events=tool_events,
                    input_guard=guard_outcome.evidence,
                )

            if result.stop_reason == "tool_use":
                messages.append({
                    "role": "assistant",
                    "content": result.raw_content,
                })
                tool_result_blocks: list[dict[str, Any]] = []

                for tool_use in result.tool_use_blocks:
                    if tools_executed >= MAX_TOOLS_PER_TURN:
                        event = ToolEvent(
                            tool_call_id=tool_use.tool_use_id,
                            tool_name=tool_use.name,
                            status=ToolStatus.DENIED.value,
                            success=False,
                            error_code="TURN_LIMIT_EXCEEDED",
                            idempotency_replayed=False,
                        )
                        tool_events.append(event)
                        tool_result_blocks.append(
                            self._make_tool_result_block(
                                tool_use.tool_use_id,
                                status="error",
                                message="單次對話最多執行兩個工具",
                                success=False,
                                tool_status=ToolStatus.DENIED.value,
                                error_code="TURN_LIMIT_EXCEEDED",
                            )
                        )
                        continue

                    if (
                        intent.expected_tool is not None
                        and tool_use.name != intent.expected_tool
                    ):
                        logger.warning(
                            "Tool intent mismatch: expected=%s actual=%s request_id=%s",
                            intent.expected_tool,
                            tool_use.name,
                            request_id,
                        )
                        mismatch_event = ToolEvent(
                            tool_call_id=tool_use.tool_use_id,
                            tool_name=tool_use.name,
                            status=ToolStatus.DENIED.value,
                            success=False,
                            error_code="TOOL_INTENT_MISMATCH",
                            idempotency_replayed=False,
                        )
                        tool_events.append(mismatch_event)
                        mismatch_reply = (
                            "工具選擇與您的需求不一致，因此這項操作尚未完成。請再試一次。"
                        )
                        self._persist_conversation_turn(
                            auth_context=auth_context,
                            user_message=guarded_message,
                            assistant_message=mismatch_reply,
                            input_type=request.input_type,
                        )
                        return ChatResponse(
                            success=True,
                            reply=mismatch_reply,
                            model=result.model,
                            session_id=session_id,
                            usage=total_usage,
                            error_type="TOOL_INTENT_MISMATCH",
                            error_message="模型選擇了不符合使用者意圖的工具",
                            operation_completed=False,
                            action_status=ActionStatus.FAILED,
                            tool_events=tool_events,
                            input_guard=guard_outcome.evidence,
                        )

                    tool_call = ToolCall(
                        tool_call_id=tool_use.tool_use_id,
                        name=tool_use.name,
                        arguments=tool_use.input,
                    )
                    gateway_result = self._gateway.execute(tool_call, auth_context)
                    tool_events.append(self._make_tool_event(gateway_result))

                    if gateway_result.status == ToolStatus.AWAITING_CONFIRMATION:
                        confirmation_reply = (
                            f"需要您的確認：{gateway_result.confirmation_summary}"
                        )
                        self._persist_conversation_turn(
                            auth_context=auth_context,
                            user_message=guarded_message,
                            assistant_message=confirmation_reply,
                            input_type=request.input_type,
                        )
                        return ChatResponse(
                            success=True,
                            reply=confirmation_reply,
                            model=result.model,
                            session_id=session_id,
                            usage=total_usage,
                            requires_confirmation=True,
                            confirmation_token=gateway_result.confirmation_token,
                            confirmation_summary=gateway_result.confirmation_summary,
                            operation_completed=False,
                            action_status=ActionStatus.CONFIRMATION_REQUIRED,
                            tool_events=tool_events,
                            input_guard=guard_outcome.evidence,
                        )

                    if gateway_result.success:
                        tools_executed += 1

                    tool_result_blocks.append(
                        self._make_tool_result_block_from_gateway(gateway_result)
                    )

                messages.append({
                    "role": "user",
                    "content": tool_result_blocks,
                })

        operation_completed, action_status = self._derive_action_status(
            intent, tool_events
        )
        logger.warning("Max Converse rounds exceeded for session %s", session_id)
        final_reply = (
            "工具已執行，但我無法完成最後回覆。"
            if operation_completed
            else "抱歉，處理過程較為複雜，請稍後再試或簡化您的請求。"
        )
        self._persist_conversation_turn(
            auth_context=auth_context,
            user_message=guarded_message,
            assistant_message=final_reply,
            input_type=request.input_type,
        )
        return ChatResponse(
            success=True,
            reply=final_reply,
            model=last_model,
            session_id=session_id,
            usage=total_usage,
            operation_completed=operation_completed,
            action_status=action_status,
            tool_events=tool_events,
            input_guard=guard_outcome.evidence,
        )

    async def _handle_confirmation(
        self,
        confirmation_token: str,
        auth_context: AuthContext,
        session_id: str,
        *,
        input_guard: InputGuardEvidence | None = None,
        user_message: str = "確認執行",
        input_type: str = "text",
    ) -> ChatResponse:
        """Execute the frozen server-side ToolCall without calling Bedrock."""
        gateway_result = self._gateway.confirm_and_execute(
            confirmation_token, auth_context
        )
        tool_event = self._make_tool_event(gateway_result)
        operation_completed = self._is_completed_write(tool_event)

        if operation_completed:
            response = ChatResponse(
                success=True,
                reply=gateway_result.message,
                model="",
                session_id=session_id,
                usage=UsageInfo(),
                operation_completed=True,
                action_status=ActionStatus.COMPLETED,
                tool_events=[tool_event],
                input_guard=input_guard,
            )
        else:
            action_status = (
                ActionStatus.DENIED
                if gateway_result.status == ToolStatus.DENIED
                else ActionStatus.FAILED
            )
            response = ChatResponse(
                success=False,
                reply=gateway_result.message or "確認失敗，這項操作尚未完成。",
                model="",
                session_id=session_id,
                usage=UsageInfo(),
                error_type=gateway_result.error_code,
                error_message=gateway_result.message,
                operation_completed=False,
                action_status=action_status,
                tool_events=[tool_event],
                input_guard=input_guard,
            )
        self._persist_conversation_turn(
            auth_context=auth_context,
            user_message=user_message,
            assistant_message=response.reply,
            input_type=input_type,
        )
        return response

    async def _handle_cancellation(
        self,
        confirmation_token: str,
        auth_context: AuthContext,
        session_id: str,
        *,
        input_guard: InputGuardEvidence | None = None,
        user_message: str = "取消操作",
        input_type: str = "text",
    ) -> ChatResponse:
        """Cancel a pending operation without invoking Bedrock or a tool handler."""
        gateway_result = self._gateway.cancel_confirmation(
            confirmation_token, auth_context
        )
        tool_event = self._make_tool_event(gateway_result)
        cancelled = gateway_result.status == ToolStatus.CANCELLED
        response = ChatResponse(
            success=cancelled,
            reply=gateway_result.message,
            model="",
            session_id=session_id,
            usage=UsageInfo(),
            error_type=None if cancelled else gateway_result.error_code,
            error_message=None if cancelled else gateway_result.message,
            operation_completed=False,
            action_status=(
                ActionStatus.CANCELLED if cancelled else ActionStatus.DENIED
            ),
            tool_events=[tool_event],
            input_guard=input_guard,
        )
        self._persist_conversation_turn(
            auth_context=auth_context,
            user_message=user_message,
            assistant_message=response.reply,
            input_type=input_type,
        )
        return response

    def _make_tool_result_block_from_gateway(
        self,
        result: ToolResult,
    ) -> dict[str, Any]:
        status = "success" if result.success else "error"
        return self._make_tool_result_block(
            result.tool_call_id,
            status=status,
            message=result.message,
            success=result.success,
            tool_status=result.status.value,
            record_id=result.record_id,
            error_code=result.error_code,
            idempotency_replayed=result.idempotency_replayed,
        )

    def _make_tool_result_block(
        self,
        tool_use_id: str,
        status: str,
        message: str,
        success: bool,
        tool_status: str,
        record_id: str | None = None,
        error_code: str | None = None,
        idempotency_replayed: bool = False,
    ) -> dict[str, Any]:
        """Create a structured Bedrock toolResult without sensitive arguments."""
        return {
            "toolResult": {
                "toolUseId": tool_use_id,
                "status": status,
                "content": [
                    {
                        "json": {
                            "success": success,
                            "status": tool_status,
                            "message": message,
                            "record_id": record_id,
                            "error_code": error_code,
                            "idempotency_replayed": idempotency_replayed,
                        }
                    }
                ],
            }
        }

    @property
    def gateway(self) -> ToolGateway:
        """Expose gateway for testing."""
        return self._gateway

    @property
    def skill_registry(self) -> SkillRegistry:
        """Expose the skill registry for testing and controlled extension."""
        return self._skill_registry
