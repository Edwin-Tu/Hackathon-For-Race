# Hackathon-For-Race

智慧長照 Agent 後端，整合：

- Amazon Bedrock Claude Haiku 4.5
- Intent Router 與 Skill Registry
- 安全 Tool Gateway
- 組員提供的 Prisma／MySQL v2 Schema
- MySQL 照護事件與提醒持久化

## 整合後資料流

```text
文字／Whisper transcript
  -> FastAPI /api/agent/chat
  -> Intent Router
  -> Skill Registry
  -> Bedrock Converse toolUse
  -> Tool Gateway（白名單、Schema、角色、確認、冪等）
  -> ToolHandlers
  -> CareRepository
       |- InMemoryCareRepository（測試／fallback）
       `- MySQLCareRepository（正式整合）
  -> care_events / reminders
  -> ToolResult + record_id
  -> Claude 最終回覆
```

Claude 與 Skill 不會取得 SQL 權限。SQL 只存在於後端的
`app/repositories/mysql.py`，而且全部使用參數化查詢。

## 主要檔案

```text
app/
├── main.py
├── services/agent_service.py
├── skills/
├── tools/
└── repositories/
    ├── base.py
    ├── memory.py
    ├── mysql.py
    └── factory.py

prisma/schema.prisma
scripts/db_prepare.py
scripts/db_integration_check.py
```

## 1. 安裝

```bash
uv sync
npm install
```

`uv sync` 會安裝 `mysql-connector-python`。

## 2. 建立 `.env`

```bash
cp .env.example .env
```

至少設定：

```dotenv
CARE_REPOSITORY_BACKEND=mysql
DATABASE_URL=mysql://smart_care_app:YOUR_PASSWORD@127.0.0.1:3306/smart_care_agent
DEMO_USER_ID=demo-user
DEMO_PERSONA_ID=demo-persona
```

AWS temporary credentials 仍由終端機環境或 boto3 credential chain 提供，
不要提交到 Git。

## 3. 同步組員的 Prisma Schema

開發資料庫可使用：

```bash
npx prisma db push
```

接著準備 Agent Demo 身分與 durable idempotency 欄位：

```bash
uv run python -m scripts.db_prepare
```

此腳本會：

1. 驗證 v2 多租戶必要資料表與欄位。
2. 在缺少時新增 `care_events.idempotency_key`。
3. 建立 Demo organization、user、persona 與存取權限。

## 4. 獨立測試資料庫 Repository

```bash
uv run python -m scripts.db_integration_check
```

成功時應看到 `care_event record_id`、`reminder record_id` 與
`schedule_count`。

## 5. 執行完整 Agent

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

測試照護事件：

```bash
curl -sS -X POST http://127.0.0.1:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "請幫我記錄：我今天下午四點散步二十分鐘。",
    "session_id": "agent-db-proof-001"
  }' | uv run python -m json.tool
```

成功條件：

- `operation_completed=true`
- `action_status=completed`
- `tool_events[0].tool_name=create_care_event`
- `tool_events[0].record_id` 非空
- MySQL `care_events` 找得到相同 `event_id`

可用 SQL 驗證：

```sql
SELECT event_id, persona_id, event_type, content, event_time, memory_status
FROM care_events
ORDER BY created_at DESC
LIMIT 5;
```

## Repository 模式

| 值 | 行為 |
|---|---|
| `memory` | 永遠使用記憶體，重啟即清空 |
| `mysql` | 必須連上 MySQL，失敗時啟動失敗 |
| `auto` | 有 `DATABASE_URL` 則 MySQL，否則記憶體 |

比賽整合階段建議明確使用 `mysql`，避免誤以為資料已持久化。

## 測試

```bash
uv run pytest -q
uv run python -m compileall -q app scripts tests
uv run python -m scripts.skill_demo
```

不需要 MySQL 的單元測試會使用 `InMemoryCareRepository`。
MySQL 真實寫入必須另外執行 `scripts.db_integration_check`。

## 尚未整合

目前資料庫整合範圍為：

- `create_care_event` -> `care_events`
- `create_reminder` -> `reminders`
- `get_user_schedule` -> `reminders` 查詢

以下仍屬後續階段：

- JWT／Cognito 取代 Demo AuthContext
- `interactions` 全回合紀錄
- `tool_executions` 與 `audit_logs` 的 MySQL adapter
- Whisper／TTS／UI
