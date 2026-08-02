# Claude 對話上下文修正

## 問題

原本 `/api/agent/chat` 每次只把本輪文字送給 Bedrock。雖然 UI 有傳 `session_id`，但後端沒有依 Session 讀取 `interactions`，所以 Claude 每輪都像新對話。

## 修正後流程

```text
UI / Voice 維持同一個 session_id
→ Input Guard
→ 後端可信任 AuthContext 取得 user_id / persona_id
→ 驗證 session_id 是否屬於相同 user + persona
→ 從 RDS interactions 載入最近對話
→ 組成 Bedrock Converse messages
→ Claude 回覆或提出 ToolCall
→ 將 user transcript + assistant response 寫回 interactions
```

## 安全邊界

- Session 綁定 `user_id + persona_id + session_id`。
- MySQL 使用 `sessions.client_identifier` 保存可信任的後端 user ID。
- 相同 `session_id` 被不同 User 或 Persona 使用時回傳 `SESSION_SCOPE_DENIED`。
- 前端不能提供或覆寫 `user_id`、`persona_id`、role。
- Input Guard BLOCK 的內容不會寫入一般對話歷史，也不會送給 Claude。
- interactions 不保存 API Token、AWS 憑證、DATABASE_URL 或 confirmation token。
- 確認操作不重新呼叫 Claude；只把確認文字與最終安全回覆寫入同一 Session。

目前雲端 Demo 仍使用 `DEMO_USER_ID` / `DEMO_PERSONA_ID`。正式登入接入後，只需把 `DemoAuthContextFactory` 替換成 JWT/Cognito 解析器；Conversation Repository 不需要重寫。

## 資料庫相容性

沒有建立新資料表，也不需要 `prisma db push`。實作直接沿用現有：

- `sessions`
- `interactions`
- `personas`
- `app_users`

同時支援舊版 Edwin RDS Schema，以及包含 organization 欄位的新版 Schema。

## 設定

```dotenv
CONVERSATION_HISTORY_ENABLED=true
CONVERSATION_HISTORY_MAX_MESSAGES=12
CONVERSATION_HISTORY_MAX_CHARS=12000
```

## 驗證

```bash
python3 -m compileall -q app scripts tests
node --check app/static/demo/app.js
python3 -m pytest -q
```

本次結果：`135 passed`。

### 同 Session 測試

第一輪：

```text
本次對話的測試代號是藍色企鵝。
```

第二輪使用相同 `session_id`：

```text
我剛才說的測試代號是什麼？
```

Claude 應回答「藍色企鵝」。改用新 Session 時不得知道答案。

## 雲端部署

```bash
source .cloud.env
scripts/cloud/deploy.sh
```

部署完成後，瀏覽器強制重新整理，再使用同一個 UI Session ID 連續測試兩輪。

## Test environment isolation fix

`tests/conftest.py` forces `CARE_REPOSITORY_BACKEND=memory` before test modules
import `app.main`. This prevents a developer `.env` that points at local or cloud
MySQL from causing pytest collection to open a real database connection. Production
and manual integration runs are unchanged; the override only exists in pytest.
