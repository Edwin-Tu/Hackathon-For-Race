#!/usr/bin/env python3
"""
Bedrock toolUse End-to-End Demo.

Validates real Bedrock Converse API with tool use against:
1. Normal chat (no toolUse)
2. Activity event (create_care_event success)
3. Medication event (awaiting_confirmation)
4. Confirmation flow (confirm_and_execute)
5. Forged persona_id (FORBIDDEN_FIELD)
6. Family write denial (role not allowed)

DOES NOT display:
- AWS credentials
- Full confirmation tokens
- Full arguments
- Sensitive source_text
- Stack traces

Requires environment variables:
- AWS_REGION
- BEDROCK_MODEL_ID
- AWS credentials (ACCESS_KEY_ID, SECRET_ACCESS_KEY, SESSION_TOKEN)
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import ChatRequest, ProviderResponse
from app.providers.bedrock import BedrockProvider
from app.services.agent_service import AgentService, SYSTEM_PROMPT
from app.tools import (
    AuthContext,
    DemoAuthContextFactory,
    ToolCall,
    ToolGateway,
    ToolStatus,
)


def mask_token(token: str | None) -> str:
    """Mask token for display, showing only first 8 chars."""
    if not token:
        return "None"
    if len(token) <= 8:
        return "***"
    return f"{token[:8]}..."


def make_event_time() -> str:
    """Create ISO timestamp with Asia/Taipei timezone."""
    taipei_tz = timezone(timedelta(hours=8))
    return datetime.now(taipei_tz).isoformat()


def print_section(title: str) -> None:
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(
    case_name: str,
    success: bool,
    stop_reason: str = "",
    tool_name: str = "",
    tool_status: str = "",
    record_id: str | None = None,
    requires_confirmation: bool = False,
    is_duplicate: bool = False,
    extra_info: str = "",
) -> None:
    """Print formatted result."""
    status_icon = "✓" if success else "✗"
    print(f"\n  [{status_icon}] {case_name}")
    if stop_reason:
        print(f"      stopReason: {stop_reason}")
    if tool_name:
        print(f"      tool_name: {tool_name}")
    if tool_status:
        print(f"      tool_status: {tool_status}")
    if record_id:
        print(f"      record_id: {record_id[:8]}...")
    if requires_confirmation:
        print(f"      requires_confirmation: True")
    if is_duplicate:
        print(f"      idempotency_replayed: True")
    if extra_info:
        print(f"      {extra_info}")


def print_response_debug(result: ProviderResponse) -> None:
    """Print response debug info without sensitive data."""
    print(f"  stopReason: {result.stop_reason}")
    if result.raw_content:
        block_types = []
        for block in result.raw_content:
            if "text" in block:
                block_types.append("text")
            elif "toolUse" in block:
                block_types.append(f"toolUse({block['toolUse']['name']})")
        print(f"  content blocks: {block_types}")
    if result.tool_use_blocks:
        for tu in result.tool_use_blocks:
            print(f"  toolUseId: {tu.tool_use_id[:12]}...")
            print(f"  tool name: {tu.name}")
            # Only show argument keys, not values
            print(f"  argument keys: {list(tu.input.keys())}")


async def call_bedrock_with_forced_tool(
    provider: BedrockProvider,
    messages: list[dict],
    tool_config: list[dict[str, Any]],
    forced_tool_name: str,
) -> ProviderResponse:
    """
    Call Bedrock with forced tool choice.
    
    This bypasses the provider's normal tool_config handling to add toolChoice.
    """
    from app.services.agent_service import SYSTEM_PROMPT
    
    # Build params manually to include toolChoice
    converse_messages = []
    for msg in messages:
        role = msg["role"]
        content = msg.get("content")
        if isinstance(content, str):
            converse_messages.append({
                "role": role,
                "content": [{"text": content}],
            })
        elif isinstance(content, list):
            converse_messages.append({
                "role": role,
                "content": content,
            })
        else:
            converse_messages.append({
                "role": role,
                "content": [{"text": str(content)}],
            })

    params = {
        "modelId": provider._model_id,
        "messages": converse_messages,
        "system": [{"text": SYSTEM_PROMPT}],
        "toolConfig": {
            "tools": tool_config,
            "toolChoice": {
                "tool": {"name": forced_tool_name}
            }
        }
    }

    try:
        response = await asyncio.to_thread(provider._sync_converse, params)
        
        from app.models import ToolUseBlock, UsageInfo
        
        output = response.get("output", {})
        message = output.get("message", {})
        content_blocks = message.get("content", [])

        text = ""
        tool_use_blocks = []

        for block in content_blocks:
            if "text" in block:
                text += block["text"]
            elif "toolUse" in block:
                tool_use = block["toolUse"]
                tool_use_blocks.append(ToolUseBlock(
                    tool_use_id=tool_use["toolUseId"],
                    name=tool_use["name"],
                    input=tool_use.get("input", {}),
                ))

        usage_data = response.get("usage", {})
        
        return ProviderResponse(
            success=True,
            text=text,
            model=provider._model_id,
            stop_reason=response.get("stopReason", ""),
            usage=UsageInfo(
                input_tokens=usage_data.get("inputTokens", 0),
                output_tokens=usage_data.get("outputTokens", 0),
                total_tokens=usage_data.get("inputTokens", 0) + usage_data.get("outputTokens", 0),
            ),
            tool_use_blocks=tool_use_blocks,
            raw_content=content_blocks,
        )
    except Exception as e:
        return ProviderResponse(
            success=False,
            error_type=type(e).__name__,
            error_message=str(e)[:100],
        )


async def demo_1_normal_chat(provider: BedrockProvider) -> bool:
    """Case 1: Normal chat should not trigger toolUse."""
    print_section("案例 1: 普通聊天 (不應產生 toolUse)")

    result = await provider.chat(
        messages=[{"role": "user", "content": "你好，請問你是誰？"}],
        system_prompt=SYSTEM_PROMPT,
        tool_config=None,
    )

    print_response_debug(result)

    success = (
        result.success
        and result.stop_reason == "end_turn"
        and len(result.tool_use_blocks) == 0
    )

    print_result(
        "普通聊天",
        success,
        stop_reason=result.stop_reason,
        extra_info=f"回覆: {result.text[:50]}..." if result.text else "",
    )
    return success


async def demo_2_activity_event(
    provider: BedrockProvider,
    gateway: ToolGateway,
) -> bool:
    """Case 2: Activity event should succeed (forced tool)."""
    print_section("案例 2: 活動事件 (create_care_event 成功)")

    auth = DemoAuthContextFactory.create_resident(
        requester_id="demo-user",
        persona_id="demo-persona",
        session_id="demo-session-2",
        request_id="demo-req-2",
    )

    tool_config = gateway.get_bedrock_tool_config(auth)
    tool_names = [t["toolSpec"]["name"] for t in tool_config]
    print(f"  Allowed tools: {tool_names}")

    # Force tool use for validation
    result1 = await call_bedrock_with_forced_tool(
        provider,
        messages=[{"role": "user", "content": "請記錄我今天下午散步三十分鐘"}],
        tool_config=tool_config,
        forced_tool_name="create_care_event",
    )

    print_response_debug(result1)

    if result1.stop_reason != "tool_use" or not result1.tool_use_blocks:
        print_result(
            "活動事件",
            False,
            stop_reason=result1.stop_reason,
            extra_info="Claude 未提出 toolUse",
        )
        return False

    tool_use = result1.tool_use_blocks[0]
    print(f"  Claude 提出: {tool_use.name}")

    # Add idempotency_key if missing
    args = dict(tool_use.input)
    if "idempotency_key" not in args:
        args["idempotency_key"] = "demo-activity-001"
    if "event_time" not in args:
        args["event_time"] = make_event_time()

    # Execute via gateway
    tool_call = ToolCall(
        tool_call_id=tool_use.tool_use_id,
        name=tool_use.name,
        arguments=args,
    )

    gateway_result = gateway.execute(tool_call, auth)

    success = (
        gateway_result.success
        and gateway_result.status == ToolStatus.SUCCEEDED
        and gateway_result.record_id is not None
    )

    print_result(
        "活動事件",
        success,
        stop_reason=result1.stop_reason,
        tool_name=tool_use.name,
        tool_status=gateway_result.status.value,
        record_id=gateway_result.record_id,
    )

    if success:
        # Second call to get final response
        messages = [
            {"role": "user", "content": "請記錄我今天下午散步三十分鐘"},
            {"role": "assistant", "content": result1.raw_content},
            {
                "role": "user",
                "content": [
                    {
                        "toolResult": {
                            "toolUseId": tool_use.tool_use_id,
                            "status": "success",
                            "content": [{"text": gateway_result.message}],
                        }
                    }
                ],
            },
        ]
        result2 = await provider.chat(
            messages=messages,
            system_prompt=SYSTEM_PROMPT,
            tool_config=tool_config,
        )
        if result2.text:
            print(f"  Claude 最終回覆: {result2.text[:60]}...")

    return success


async def demo_3_medication_event(
    provider: BedrockProvider,
    gateway: ToolGateway,
) -> tuple[bool, str | None, ToolCall | None, AuthContext | None]:
    """Case 3: Medication event should require confirmation (forced tool)."""
    print_section("案例 3: 用藥事件 (awaiting_confirmation)")

    auth = DemoAuthContextFactory.create_resident(
        requester_id="demo-user",
        persona_id="demo-persona",
        session_id="demo-session-3",
        request_id="demo-req-3",
    )

    tool_config = gateway.get_bedrock_tool_config(auth)
    tool_names = [t["toolSpec"]["name"] for t in tool_config]
    print(f"  Allowed tools: {tool_names}")

    # Force tool use for validation
    result1 = await call_bedrock_with_forced_tool(
        provider,
        messages=[{"role": "user", "content": "請記錄我早上八點吃了降血壓藥"}],
        tool_config=tool_config,
        forced_tool_name="create_care_event",
    )

    print_response_debug(result1)

    if result1.stop_reason != "tool_use" or not result1.tool_use_blocks:
        print_result(
            "用藥事件",
            False,
            stop_reason=result1.stop_reason,
            extra_info="Claude 未提出 toolUse",
        )
        return False, None, None, None

    tool_use = result1.tool_use_blocks[0]
    print(f"  Claude 提出: {tool_use.name}")

    # Add required fields
    args = dict(tool_use.input)
    if "idempotency_key" not in args:
        args["idempotency_key"] = "demo-med-001"
    if "event_time" not in args:
        args["event_time"] = make_event_time()
    # Ensure it's medication type
    args["event_type"] = "medication"

    tool_call = ToolCall(
        tool_call_id=tool_use.tool_use_id,
        name=tool_use.name,
        arguments=args,
    )

    gateway_result = gateway.execute(tool_call, auth)

    success = (
        gateway_result.status == ToolStatus.AWAITING_CONFIRMATION
        and gateway_result.requires_confirmation
        and gateway_result.confirmation_token is not None
    )

    print_result(
        "用藥事件",
        success,
        stop_reason=result1.stop_reason,
        tool_name=tool_use.name,
        tool_status=gateway_result.status.value,
        requires_confirmation=gateway_result.requires_confirmation,
        extra_info=f"confirmation_token: {mask_token(gateway_result.confirmation_token)}",
    )

    # Verify no record created yet
    events = gateway.repository.get_all_events()
    med_events = [e for e in events if e.event_type == "medication"]
    if med_events:
        print("  ⚠ 警告: 尚未確認但已建立紀錄!")
        success = False
    else:
        print("  ✓ 確認: 尚未建立紀錄 (正確)")

    return success, gateway_result.confirmation_token, tool_call, auth


async def demo_4_confirmation_flow(
    gateway: ToolGateway,
    token: str,
    auth: AuthContext,
) -> bool:
    """Case 4: Confirmation flow should succeed once and reject duplicate."""
    print_section("案例 4: 確認流程")

    # Step 1: Confirm
    gateway_result = gateway.confirm_and_execute(token, auth)

    success1 = (
        gateway_result.success
        and gateway_result.status == ToolStatus.SUCCEEDED
        and gateway_result.record_id is not None
    )

    print_result(
        "確認執行",
        success1,
        tool_name="create_care_event",
        tool_status=gateway_result.status.value,
        record_id=gateway_result.record_id,
    )

    # Count medication events
    events = gateway.repository.get_all_events()
    med_events = [e for e in events if e.event_type == "medication"]
    print(f"  用藥紀錄數: {len(med_events)}")

    # Step 2: Try to reuse same token
    gateway_result2 = gateway.confirm_and_execute(token, auth)

    success2 = (
        not gateway_result2.success
        and gateway_result2.error_code == "INVALID_CONFIRMATION"
    )

    print_result(
        "重複使用 token",
        success2,
        tool_status=gateway_result2.status.value,
        extra_info=f"error_code: {gateway_result2.error_code}" if gateway_result2.error_code else "",
    )

    # Verify still only 1 record
    events = gateway.repository.get_all_events()
    med_events = [e for e in events if e.event_type == "medication"]
    no_duplicate = len(med_events) == 1
    print(f"  確認後用藥紀錄數: {len(med_events)} (應為 1)")

    return success1 and success2 and no_duplicate


def demo_5_forged_persona_id(gateway: ToolGateway) -> bool:
    """Case 5: Forged persona_id should be rejected."""
    print_section("案例 5: 非法 persona_id (FORBIDDEN_FIELD)")

    auth = DemoAuthContextFactory.create_resident(
        requester_id="demo-user",
        persona_id="demo-persona",
        session_id="demo-session-5",
        request_id="demo-req-5",
    )

    # Construct tool call with forged persona_id
    tool_call = ToolCall(
        tool_call_id="forged-001",
        name="create_care_event",
        arguments={
            "event_type": "activity",
            "content": "測試偽造 persona_id",
            "event_time": make_event_time(),
            "persona_id": "hacked-persona",  # Forged!
            "idempotency_key": "demo-forged-001",
        },
    )

    gateway_result = gateway.execute(tool_call, auth)

    success = (
        not gateway_result.success
        and gateway_result.status == ToolStatus.DENIED
        and gateway_result.error_code == "FORBIDDEN_FIELD"
    )

    print_result(
        "偽造 persona_id",
        success,
        tool_name="create_care_event",
        tool_status=gateway_result.status.value,
        extra_info=f"error_code: {gateway_result.error_code}" if gateway_result.error_code else "",
    )

    return success


def demo_6_family_write_denied(gateway: ToolGateway) -> bool:
    """Case 6: Family role should not see write tools and be rejected if forged."""
    print_section("案例 6: Family 寫入 (ROLE_NOT_ALLOWED)")

    # Use correct parameter name: authorized_persona_ids (set, not list)
    auth = DemoAuthContextFactory.create_family(
        requester_id="family-user",
        authorized_persona_ids={"demo-persona"},  # set, not list
        session_id="demo-session-6",
        request_id="demo-req-6",
    )

    # Step 1: Check that family cannot see write tools
    tool_config = gateway.get_bedrock_tool_config(auth)
    tool_names = [t["toolSpec"]["name"] for t in tool_config]

    has_write_tools = any(
        name in tool_names for name in ["create_care_event", "create_reminder"]
    )

    print(f"  Family 可見工具: {tool_names}")
    print(f"  包含寫入工具: {has_write_tools} (應為 False)")

    # Step 2: Even if forged, should be rejected
    tool_call = ToolCall(
        tool_call_id="family-forged-001",
        name="create_care_event",
        arguments={
            "event_type": "activity",
            "content": "家屬偽造寫入",
            "event_time": make_event_time(),
            "idempotency_key": "demo-family-001",
        },
    )

    gateway_result = gateway.execute(tool_call, auth)

    forged_rejected = (
        not gateway_result.success
        and gateway_result.status == ToolStatus.DENIED
        and gateway_result.error_code == "ROLE_NOT_ALLOWED"
    )

    print_result(
        "Family 偽造 toolUse",
        forged_rejected,
        tool_name="create_care_event",
        tool_status=gateway_result.status.value,
        extra_info=f"error_code: {gateway_result.error_code}" if gateway_result.error_code else "",
    )

    success = not has_write_tools and forged_rejected
    return success


async def main() -> None:
    """Run all demo cases."""
    print("=" * 60)
    print("  Bedrock toolUse End-to-End Demo")
    print("  智慧長照語音 Agent - 真實 Bedrock 驗證")
    print("=" * 60)

    # Check environment
    region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION"))
    model_id = os.environ.get("BEDROCK_MODEL_ID")

    if not region:
        print("\n錯誤: 未設定 AWS_REGION 或 AWS_DEFAULT_REGION")
        sys.exit(1)

    if not model_id:
        print("\n錯誤: 未設定 BEDROCK_MODEL_ID")
        sys.exit(1)

    print(f"\n  Region: {region}")
    print(f"  Model:  {model_id}")

    # Initialize
    provider = BedrockProvider()
    gateway = ToolGateway()

    results: dict[str, bool] = {}

    try:
        # Demo 1: Normal chat
        results["1. 普通聊天"] = await demo_1_normal_chat(provider)

        # Demo 2: Activity event (forced tool)
        results["2. 活動事件"] = await demo_2_activity_event(provider, gateway)

        # Demo 3: Medication event (forced tool)
        success3, token, tool_call, auth = await demo_3_medication_event(
            provider, gateway
        )
        results["3. 用藥事件"] = success3

        # Demo 4: Confirmation flow
        if token and auth:
            results["4. 確認流程"] = await demo_4_confirmation_flow(gateway, token, auth)
        else:
            print_section("案例 4: 確認流程")
            print("  跳過: 案例 3 未產生 confirmation_token")
            results["4. 確認流程"] = False

        # Demo 5: Forged persona_id
        results["5. 非法 persona_id"] = demo_5_forged_persona_id(gateway)

        # Demo 6: Family write denied
        results["6. Family 寫入"] = demo_6_family_write_denied(gateway)

    except Exception as e:
        # Don't show full stack trace
        print(f"\n錯誤: {type(e).__name__}: {str(e)[:100]}")
        sys.exit(1)

    # Summary
    print_section("結果摘要")
    all_passed = True
    for name, passed in results.items():
        icon = "✓" if passed else "✗"
        print(f"  [{icon}] {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("  所有案例通過!")
    else:
        print("  部分案例失敗")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
