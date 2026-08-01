# Confirmation Resume 修正

## 問題

第一輪建立高風險提醒或用藥事件時，Tool Gateway 會回傳 `requires_confirmation=true`。但第二輪使用者只輸入「確認」時，舊流程會把它當成新的 Agent 對話，重新呼叫 Claude，因此原本的待確認工具不一定會被執行。

## 修正後流程

```text
第一輪工具提案
→ Tool Gateway 驗證並凍結完整 ToolCall
→ 伺服器保存 token / session / requester / role / args hash
→ API 回傳 opaque confirmation_token 與 summary

第二輪「確認」或確認按鈕
→ 依 trusted session 找回 pending ToolCall
→ 不呼叫 Bedrock
→ 不重新接受工具參數
→ confirm_and_execute()
→ 寫入 MySQL
→ token 單次使用
```

## 新增能力

- `POST /api/agent/confirm`
- `decision=confirm|cancel`
- 文字或語音輸入「確認」可自動續接同一 Session 的待確認操作
- 文字或語音輸入「取消」可撤銷待確認操作
- UI 新增「確認執行」與「取消」按鈕
- Confirmation Token 綁定 `session_id`、`requester_id`、`role`
- 每個 Session/使用者只保留一筆有效待確認操作，避免確認歧義
- 確認與取消流程不呼叫 Claude，Token usage 為 0
- 伺服器端保存凍結後的 ToolCall，前端不能重送或修改工具參數

## 相容性

原本在 `/api/agent/chat` 直接附上 `confirmation_token` 的方式仍保留，但 UI 改用專用 `/api/agent/confirm` 端點。

## 驗證

```text
120 passed in 6.07s
Python compileall passed
JavaScript syntax check passed
```
