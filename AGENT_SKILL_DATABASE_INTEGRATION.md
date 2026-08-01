# Agent + Skill + Database 整合報告

## 本次基準

- Agent／Tool Gateway 基準：`Hackathon-For-Race-with-skills`
- 資料庫基準：組員的 `Hackathon-For-Race-main-with-skills`

沒有以組員的簡易 `bedrock_client.py` 取代現有 Agent；保留已驗證的
Bedrock tool-use loop、Skill Registry 與 Tool Gateway，僅將 Repository
從記憶體抽象成可切換的 MySQL adapter。

## 已整合

1. 複製組員的 `prisma/`、MySQL 帳號 SQL 與授權 middleware。
2. 新增 `CareRepository` 契約。
3. 保留 `InMemoryCareRepository` 作為測試與 fallback。
4. 新增 `MySQLCareRepository`：
   - 依 persona 解析 organization tenant。
   - 寫入 `care_events`。
   - 寫入 `reminders`。
   - 依 Asia/Taipei 日期查詢提醒。
   - 儲存 UTC，輸出時轉回 Asia/Taipei。
   - 使用參數化 SQL。
5. `ToolHandlers` 現在傳遞 `source_text` 與 `idempotency_key`。
6. `app.main` 依環境建立 Memory 或 MySQL Repository。
7. Demo AuthContext ID 改由 `.env` 注入。
8. `care_events` 新增唯一 `idempotency_key`，使重啟後仍能防止重複寫入。
9. 新增 DB prepare 與 smoke check 腳本。

## 安全邊界

沒有把資料庫工具暴露給 Claude：

```text
Claude -> toolUse proposal
Tool Gateway -> validate/authorize/confirm
ToolHandlers -> fixed repository methods
MySQL Repository -> parameterized SQL
```

模型不能指定 `persona_id`、`organization_id`、資料表、SQL 或任意查詢。

## 驗證

在無 MySQL 的建置環境完成：

```text
82 passed
compileall passed
```

因建置環境沒有使用者的 MySQL 與 credentials，未聲稱完成真實資料庫
端到端測試。請在 Mac 執行：

```bash
uv sync
npx prisma db push
uv run python -m scripts.db_prepare
uv run python -m scripts.db_integration_check
```

接著啟動 FastAPI 並進行真實 Bedrock 寫入測試。
