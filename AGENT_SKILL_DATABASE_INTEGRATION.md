# Agent + Skill + Input Guard + Database integration

此版本以實際運行中的 MySQL Schema 為準，不再使用舊草稿中的
`care_events`／`organizations` 假設。

## 已整合

- `create_care_event` 寫入 `events`
- `create_reminder` 寫入 `reminders`
- `get_user_schedule` 查詢 `reminders`
- `persona_id` 由後端 `AuthContext` 注入
- `created_by_id` 使用已存在的 `app_users.user_id`
- API session 字串不直接寫入資料庫外鍵欄位
- Input Guard 在 Bedrock 與 Skill 之前執行
- 阻擋時不呼叫模型、不呼叫 Tool Gateway、不寫入 MySQL

## 現有資料庫

目前正式對接的資料表包括：

- `app_users`
- `personas`
- `user_persona_access`
- `events`
- `reminders`
- `sessions`
- `interactions`
- `tool_executions`
- `audit_logs`

不要對既有資料庫執行舊 Prisma 草稿的 `db push`。

## 驗證

- Agent 回傳的 `record_id` 已與 MySQL `events.event_id` 對上。
- 台灣時間先轉成 UTC 後寫入資料庫。
- Input Guard dataset 180 / 180。
- 專案自動測試 100 passed。
