"""Agent service: orchestrates Bedrock calls with a guarded tool loop."""

import logging
import uuid
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.models import (
    ActionStatus,
    ChatRequest,
    ChatResponse,
    ToolEvent,
    UsageInfo,
)
from app.providers.base import BaseLLMProvider
from app.services.intent_router import IntentDecision, RequestedAction, classify_intent
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

SYSTEM_PROMPT_TEMPLATE = """你是一個智慧長照生活協助系統。請嚴格遵守以下規則：

目前時間：{current_datetime}
目前日期：{current_date}
系統時區：Asia/Taipei
所有「今天、明天、剛剛、下午、晚上」等相對時間，都必須以上述伺服器時間為基準，不得自行猜測其他年份或日期。
若使用者只提供「今天下午」等模糊時段而沒有明確時刻，請針對缺少的時刻詢問，不得自行填入固定時間。

回覆語言與格式：
- 一律使用繁體中文。
- 每次回覆限制在二到四句話。
- 不得使用 Markdown 格式、標題符號、星號粗體、項目符號或程式碼區塊。
- 不得使用 Emoji 或表情符號。
- 使用自然、簡單、適合語音朗讀的完整句子。

內容規則：
- 你的定位是生活協助，包含日常提醒、生活建議與情緒陪伴。
- 不得提供醫療診斷或藥物調整建議；醫療問題應建議諮詢專業醫療人員。
- 工具請求只是提案，不代表操作已完成。
- 尚未真的執行工具時，不得宣稱「已記錄」、「已建立提醒」、「已保存」或「已通知照護人員」。
- 只有工具回傳 success=true、status=succeeded，且寫入工具具有 record_id 時，才能告知使用者寫入操作已完成。
- 使用者只是詢問功能時，只需簡短說明主要能力。

工具路由規則：
- 使用者要求「記錄、記下、保存」已發生事件時，只能使用 create_care_event。
- 使用者要求「提醒我、建立提醒、設定提醒」時，只能使用 create_reminder。
- 使用者要求「查看、查詢、有什麼行程」時，只能使用 get_user_schedule。
- get_user_schedule 是唯讀工具，不得用它代替新增或記錄事件。
- 不得要求或自行產生 persona_id、resident_id 或其他授權欄位。
- 若工具需要確認，請告知需要確認的內容，但不得提及確認代碼。
- 若工具執行失敗或被拒絕，請明確說明尚未完成，不得捏造 record_id。
"""

MAX_CONVERSE_ROUNDS = 3
MAX_TOOLS_PER_TURN = 2


class AgentService:
    """Service that handles chat logic with intent-constrained tool use."""

    def __init__(
        self,
        provider: BaseLLMProvider,
        gateway: ToolGateway | None = None,
    ) -> None:
        self._provider = provider
        self._gateway = gateway or ToolGateway()

    def _create_demo_auth_context(
        self,
        session_id: str,
        request_id: str,
    ) -> AuthContext:
        """Create development-only auth context."""
        return DemoAuthContextFactory.create_resident(
            requester_id="demo-user",
            persona_id="demo-persona",
            session_id=session_id,
            request_id=request_id,
        )

    def _build_system_prompt(self) -> str:
        """Build a prompt containing trusted server date/time."""
        now = datetime.now(TAIPEI_TZ)
        return SYSTEM_PROMPT_TEMPLATE.format(
            current_datetime=now.isoformat(timespec="seconds"),
            current_date=now.date().isoformat(),
        )

    def _build_tool_configs(
        self,
        auth_context: AuthContext,
        intent: IntentDecision,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """Build initial and follow-up Bedrock toolConfig objects.

        Only the expected tool is exposed for an explicit intent. The first
        round may force that tool when the utterance contains enough time
        information. Follow-up rounds remove toolChoice so the model can end
        the turn after receiving toolResult.
        """
        if intent.expected_tool is None:
            return None, None

        all_specs = self._gateway.get_bedrock_tool_config(auth_context)
        filtered = [
            item
            for item in all_specs
            if item.get("toolSpec", {}).get("name") == intent.expected_tool
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

        self._gateway.reset_turn_count(request_id)
        intent = classify_intent(request.message)
        initial_tool_config, follow_up_tool_config = self._build_tool_configs(
            auth_context, intent
        )

        messages: list[dict[str, Any]] = [
            {"role": "user", "content": request.message}
        ]
        total_usage = UsageInfo()
        tools_executed = 0
        tool_events: list[ToolEvent] = []
        system_prompt = self._build_system_prompt()
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
                return ChatResponse(
                    success=True,
                    reply=reply,
                    model=result.model,
                    session_id=session_id,
                    usage=total_usage,
                    operation_completed=operation_completed,
                    action_status=action_status,
                    tool_events=tool_events,
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
                        return ChatResponse(
                            success=True,
                            reply="工具選擇與您的需求不一致，因此這項操作尚未完成。請再試一次。",
                            model=result.model,
                            session_id=session_id,
                            usage=total_usage,
                            error_type="TOOL_INTENT_MISMATCH",
                            error_message="模型選擇了不符合使用者意圖的工具",
                            operation_completed=False,
                            action_status=ActionStatus.FAILED,
                            tool_events=tool_events,
                        )

                    tool_call = ToolCall(
                        tool_call_id=tool_use.tool_use_id,
                        name=tool_use.name,
                        arguments=tool_use.input,
                    )
                    gateway_result = self._gateway.execute(tool_call, auth_context)
                    tool_events.append(self._make_tool_event(gateway_result))

                    if gateway_result.status == ToolStatus.AWAITING_CONFIRMATION:
                        return ChatResponse(
                            success=True,
                            reply=f"需要您的確認：{gateway_result.confirmation_summary}",
                            model=result.model,
                            session_id=session_id,
                            usage=total_usage,
                            requires_confirmation=True,
                            confirmation_token=gateway_result.confirmation_token,
                            confirmation_summary=gateway_result.confirmation_summary,
                            operation_completed=False,
                            action_status=ActionStatus.CONFIRMATION_REQUIRED,
                            tool_events=tool_events,
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
        return ChatResponse(
            success=True,
            reply=(
                "工具已執行，但我無法完成最後回覆。"
                if operation_completed
                else "抱歉，處理過程較為複雜，請稍後再試或簡化您的請求。"
            ),
            model=last_model,
            session_id=session_id,
            usage=total_usage,
            operation_completed=operation_completed,
            action_status=action_status,
            tool_events=tool_events,
        )

    async def _handle_confirmation(
        self,
        confirmation_token: str,
        auth_context: AuthContext,
        session_id: str,
    ) -> ChatResponse:
        """Handle confirmation of a pending tool operation."""
        gateway_result = self._gateway.confirm_and_execute(
            confirmation_token, auth_context
        )
        tool_event = self._make_tool_event(gateway_result)
        operation_completed = self._is_completed_write(tool_event)

        if operation_completed:
            return ChatResponse(
                success=True,
                reply=gateway_result.message,
                model="",
                session_id=session_id,
                usage=UsageInfo(),
                operation_completed=True,
                action_status=ActionStatus.COMPLETED,
                tool_events=[tool_event],
            )

        action_status = (
            ActionStatus.DENIED
            if gateway_result.status == ToolStatus.DENIED
            else ActionStatus.FAILED
        )
        return ChatResponse(
            success=False,
            reply="",
            model="",
            session_id=session_id,
            usage=UsageInfo(),
            error_type=gateway_result.error_code,
            error_message=gateway_result.message,
            operation_completed=False,
            action_status=action_status,
            tool_events=[tool_event],
        )

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
