# 修正摘要

本次修正針對「使用者要求記錄照護事件，但 Claude 誤選 `get_user_schedule`，API 卻仍回報 `operation_completed=true`」的問題。

## 核心修正

1. 新增確定性意圖路由 `app/services/intent_router.py`
   - 記錄／記下／保存已發生事件 → `create_care_event`
   - 提醒我／建立提醒 → `create_reminder`
   - 查看／查詢行程 → `get_user_schedule`
   - 明確時間會強制指定正確工具；模糊時段不強制，允許模型詢問補充資訊。

2. 限制 Bedrock 可見工具
   - 明確意圖時只暴露對應工具。
   - 首輪可使用 `toolChoice` 強制正確工具。
   - 收到 `toolResult` 後移除強制選擇，避免重複呼叫。

3. 新增工具與意圖不一致防護
   - 寫入意圖若模型選到唯讀工具，直接回傳 `TOOL_INTENT_MISMATCH`。
   - 錯誤工具不會進入 Tool Gateway handler，也不會建立資料。

4. 修正完成狀態判定
   - `operation_completed=true` 僅限寫入工具：
     - `success=true`
     - `status=succeeded`
     - `record_id` 非空
   - `get_user_schedule` 成功改為 `action_status=query_completed`，不再視為寫入完成。

5. 防止模型虛假成功宣告
   - 沒有後端寫入證據時，回覆不可包含「已記錄／已建立／已保存／已完成」。

6. 使用伺服器可信時間
   - System Prompt 注入 `Asia/Taipei` 的目前日期與時間。
   - 相對日期不得自行猜測其他年份。
   - In-memory 行程查詢預設日期也改用台北時區。

7. ToolResult 改為結構化 JSON
   - 回傳 `success`、`status`、`record_id`、`error_code`、`idempotency_replayed`。
   - 不包含工具完整參數或敏感資訊。

## 驗證結果

```text
66 passed in 5.60s
```

執行指令：

```bash
PYTHONPATH=. python3 -m pytest -q
PYTHONPATH=. python3 -m compileall -q app scripts tests
```

在原本 Mac 專案環境中也可執行：

```bash
uv run pytest -q
uv run python -m compileall -q app scripts tests
```
