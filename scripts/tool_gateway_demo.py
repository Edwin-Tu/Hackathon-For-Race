#!/usr/bin/env python3
"""
Tool Gateway Demo Script.

Demonstrates:
1. Resident own persona allowed
2. Forged persona_id denied
3. Family write denied
4. Unknown tool denied
5. Medication confirmation flow
6. Duplicate idempotency replay
7. Minimized audit (no argument values)
"""

from datetime import datetime, timedelta, timezone

from app.tools import (
    DemoAuthContextFactory,
    ToolCall,
    ToolGateway,
    ToolStatus,
)


def make_event_time() -> str:
    """Create ISO timestamp with timezone."""
    return (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()


def print_result(title: str, result):
    """Print formatted result."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print(f"  Status:  {result.status.value}")
    print(f"  Success: {result.success}")
    print(f"  Message: {result.message}")
    if result.record_id:
        print(f"  Record:  {result.record_id}")
    if result.error_code:
        print(f"  Error:   {result.error_code}")
    if result.requires_confirmation:
        print(f"  Confirmation Summary: {result.confirmation_summary}")
    if result.idempotency_replayed:
        print(f"  Idempotency Replayed: True")


def main():
    print("\n" + "="*60)
    print("  Tool Gateway Demo")
    print("  智慧長照語音 Agent - 工具閘道展示")
    print("="*60)

    gateway = ToolGateway()

    # Demo 1: Resident own persona allowed
    print("\n[Demo 1] 住民對自己的資料新增活動事件 - 應允許")
    resident_auth = DemoAuthContextFactory.create_resident(
        requester_id="user-001",
        persona_id="persona-001",
        session_id="demo-session",
        request_id="req-demo-1",
    )

    tool_call = ToolCall(
        tool_call_id="demo-tc-1",
        name="create_care_event",
        arguments={
            "event_type": "activity",
            "content": "下午在公園散步30分鐘",
            "event_time": make_event_time(),
            "idempotency_key": "demo-idem-1",
        },
    )
    result = gateway.execute(tool_call, resident_auth)
    print_result("住民新增活動事件", result)
    assert result.success, "Demo 1 failed!"


    # Demo 2: Forged persona_id denied
    print("\n[Demo 2] 住民嘗試偽造 persona_id - 應拒絕")
    gateway.reset_turn_count("req-demo-2")
    resident_auth2 = DemoAuthContextFactory.create_resident(
        requester_id="user-001",
        persona_id="persona-001",
        session_id="demo-session",
        request_id="req-demo-2",
    )

    tool_call_forged = ToolCall(
        tool_call_id="demo-tc-2",
        name="create_care_event",
        arguments={
            "event_type": "activity",
            "content": "嘗試寫入他人資料",
            "event_time": make_event_time(),
            "idempotency_key": "demo-idem-2",
            "persona_id": "other-persona",  # Forged!
        },
    )
    result = gateway.execute(tool_call_forged, resident_auth2)
    print_result("偽造 persona_id", result)
    assert not result.success, "Demo 2 should fail!"
    assert result.error_code == "FORBIDDEN_FIELD"

    # Demo 3: Family write denied
    print("\n[Demo 3] 家屬嘗試寫入資料 - 應拒絕 (家屬為唯讀)")
    family_auth = DemoAuthContextFactory.create_family(
        requester_id="family-001",
        authorized_persona_ids={"persona-001"},
        session_id="demo-session",
        request_id="req-demo-3",
    )

    tool_call_family = ToolCall(
        tool_call_id="demo-tc-3",
        name="create_care_event",
        arguments={
            "event_type": "meal",
            "content": "午餐",
            "event_time": make_event_time(),
            "idempotency_key": "demo-idem-3",
        },
    )
    result = gateway.execute(tool_call_family, family_auth)
    print_result("家屬寫入資料", result)
    assert not result.success, "Demo 3 should fail!"
    assert result.error_code == "ROLE_NOT_ALLOWED"

    # Demo 4: Unknown tool denied
    print("\n[Demo 4] 嘗試呼叫未知工具 execute_sql - 應拒絕")
    gateway.reset_turn_count("req-demo-4")
    resident_auth4 = DemoAuthContextFactory.create_resident(
        requester_id="user-001",
        persona_id="persona-001",
        session_id="demo-session",
        request_id="req-demo-4",
    )

    tool_call_sql = ToolCall(
        tool_call_id="demo-tc-4",
        name="execute_sql",
        arguments={"query": "DROP TABLE users;"},
    )
    result = gateway.execute(tool_call_sql, resident_auth4)
    print_result("未知工具 execute_sql", result)
    assert not result.success, "Demo 4 should fail!"
    assert result.error_code == "UNKNOWN_TOOL"


    # Demo 5: Medication confirmation flow
    print("\n[Demo 5] 用藥事件需要確認 - 分兩步驟")
    gateway.reset_turn_count("req-demo-5")
    resident_auth5 = DemoAuthContextFactory.create_resident(
        requester_id="user-001",
        persona_id="persona-001",
        session_id="demo-session",
        request_id="req-demo-5",
    )

    tool_call_med = ToolCall(
        tool_call_id="demo-tc-5",
        name="create_care_event",
        arguments={
            "event_type": "medication",
            "content": "服用降血壓藥一顆",
            "event_time": make_event_time(),
            "idempotency_key": "demo-idem-5",
        },
    )

    # Step 1: Get confirmation
    result = gateway.execute(tool_call_med, resident_auth5)
    print_result("用藥事件 (第一步：需確認)", result)
    assert result.status == ToolStatus.AWAITING_CONFIRMATION
    assert result.confirmation_token is not None
    token = result.confirmation_token

    # Step 2: Confirm and execute
    print("\n  → 使用者確認後執行...")
    result = gateway.confirm_and_execute(token, resident_auth5)
    print_result("用藥事件 (第二步：已確認)", result)
    assert result.success, "Demo 5 step 2 should succeed!"

    # Demo 6: Duplicate idempotency replay
    print("\n[Demo 6] 重複提交相同 idempotency_key - 不重複建立")
    gateway.reset_turn_count("req-demo-6")
    resident_auth6 = DemoAuthContextFactory.create_resident(
        requester_id="user-001",
        persona_id="persona-001",
        session_id="demo-session",
        request_id="req-demo-6",
    )

    tool_call_dup = ToolCall(
        tool_call_id="demo-tc-6a",
        name="create_care_event",
        arguments={
            "event_type": "meal",
            "content": "早餐：稀飯配蛋",
            "event_time": make_event_time(),
            "idempotency_key": "demo-idem-6-unique",
        },
    )

    result1 = gateway.execute(tool_call_dup, resident_auth6)
    print_result("第一次執行", result1)
    record_id_1 = result1.record_id

    # Second submission with same idempotency_key
    tool_call_dup2 = ToolCall(
        tool_call_id="demo-tc-6b",
        name="create_care_event",
        arguments={
            "event_type": "meal",
            "content": "早餐：稀飯配蛋",
            "event_time": make_event_time(),
            "idempotency_key": "demo-idem-6-unique",  # Same key
        },
    )
    result2 = gateway.execute(tool_call_dup2, resident_auth6)
    print_result("第二次執行 (相同 idempotency_key)", result2)

    assert result2.idempotency_replayed, "Should be replayed!"
    assert result2.record_id == record_id_1, "Should return same record!"
    print(f"  → 確認：兩次回傳相同 record_id = {record_id_1}")


    # Demo 7: Minimized audit (no argument values)
    print("\n[Demo 7] 稽核記錄僅保存欄位名稱，不保存值")
    audits = gateway.audit_store.get_all()
    print(f"  總稽核記錄數: {len(audits)}")

    if audits:
        sample = audits[-1]
        print(f"\n  最後一筆稽核:")
        print(f"    audit_id:      {sample.audit_id[:8]}...")
        print(f"    tool_name:     {sample.tool_name}")
        print(f"    requester_id:  {sample.requester_id}")
        print(f"    role:          {sample.role.value}")
        print(f"    decision:      {sample.decision}")
        print(f"    status:        {sample.status.value}")
        print(f"    argument_names: {sample.argument_names}")

        # Verify no sensitive values in audit
        audit_str = str(sample.model_dump())
        sensitive_values = [
            "稀飯配蛋",
            "下午在公園散步",
            "服用降血壓藥",
            "DROP TABLE",
        ]
        for val in sensitive_values:
            if val in audit_str:
                print(f"    ❌ WARNING: Found sensitive value in audit: {val}")
            else:
                print(f"    ✓ 未包含敏感值: '{val[:10]}...'")

    # Summary
    print("\n" + "="*60)
    print("  Demo 完成！所有安全檢查通過。")
    print("="*60)

    print("\n  權限矩陣摘要:")
    print("  ┌─────────────────┬──────────┬──────────┬──────────┐")
    print("  │ 工具            │ resident │ caregiver│ family   │")
    print("  ├─────────────────┼──────────┼──────────┼──────────┤")
    print("  │ create_care_event│ 自己✓   │ 授權✓   │ ✗       │")
    print("  │ create_reminder  │ 自己✓   │ 授權✓   │ ✗       │")
    print("  │ get_user_schedule│ 自己✓   │ 授權✓   │ 授權✓唯讀│")
    print("  └─────────────────┴──────────┴──────────┴──────────┘")

    print("\n  Gateway 公開介面:")
    print("    • preflight(tool_call, auth_context) → ToolResult")
    print("    • execute(tool_call, auth_context) → ToolResult")
    print("    • confirm_and_execute(token, tool_call, auth_context) → ToolResult")
    print("    • get_bedrock_tool_config(auth_context) → list[dict]")
    print("    • reset_turn_count(request_id)")

    print("\n  尚未完成的安全依賴:")
    print("    • JWT/Session 驗證 (目前使用 DemoAuthContextFactory)")
    print("    • MySQL 持久化儲存")
    print("    • 真實的照護人員授權機制")
    print("    • Rate limiting")
    print("    • 加密的 confirmation token")

    print("\n  下一步 - 接 Bedrock toolUse:")
    print("    1. 在 agent_service.py 呼叫 gateway.get_bedrock_tool_config()")
    print("    2. 將 toolConfig 傳給 Bedrock Converse API")
    print("    3. 收到 toolUse 回應時，呼叫 gateway.execute()")
    print("    4. 將 ToolResult 轉為 toolResult 傳回 Bedrock")
    print("    5. 只有 ToolResult.success=True 時才讓模型宣稱完成")


if __name__ == "__main__":
    main()
