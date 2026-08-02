# Backend Hardening v4

本版本只修改後端整合、資料隔離與錯誤處理；`app/static/` 完全未變更，因此 UI 版面、配色與互動設計不受影響。

## 修正項目

1. **待確認 ToolCall 持久化**
   - MySQL/RDS 模式會將待確認操作寫入既有 `confirmation_requests` 與 `tool_executions`。
   - 資料只保存確認 Token 的 SHA-256 雜湊，不保存原始 Token。
   - ToolCall 綁定 user、role、session、persona、參數雜湊與 TTL。
   - ECS Task 替換或重啟後仍可繼續確認。
   - Token 維持單次使用，並在確認時重新驗證權限與參數。

2. **工具 Timeout 不再被 executor shutdown 阻塞**
   - 超過 timeout 後 HTTP 請求可立即返回 `TOOL_TIMEOUT`。
   - 不再因 `ThreadPoolExecutor.__exit__` 等待背景 worker 而失去 timeout 效果。

3. **照護事件資料庫層冪等**
   - `care_events.idempotency_key` 存在時，MySQL repository 會先查重並處理唯一鍵競爭。
   - 即使 ECS 重啟或兩個請求同時送達，也會回傳原始 `event_id`，避免重複寫入。
   - `scripts/db_prepare.py` 已能補上缺少的欄位與唯一索引。

4. **提醒輸出事件隔離**
   - `/api/output/events` 固定限制在後端可信任的 Demo Persona。
   - 可額外用 `session_id` 篩選。
   - 不更改既有回傳結構，舊 UI 可直接使用。

5. **Tool Gateway 稽核持久化**
   - MySQL/RDS 模式會將去識別化稽核資料寫入既有 `audit_logs`。
   - 僅保存參數名稱，不保存照護內容、source_text、Token 或資料庫密碼。
   - 稽核資料庫暫時失敗時，工具安全決策仍會完成並留下後端錯誤日誌。

6. **長時間運行記憶體控制**
   - Tool turn counter 改為有界 `OrderedDict`，最多保留 4096 個 request ID。

## 驗證

```text
141 passed
Python compileall passed
JavaScript syntax check passed
Secret scan passed
app/static diff: no changes
```

`npx prisma validate` 在產出環境因內部 npm registry 無法取得 Prisma CLI 而未執行；本次沒有修改 `prisma/schema.prisma`。

## 套用

```bash
cd ~/黑客松比賽/Hackathon-For-Race

git apply --check ~/Downloads/Hackathon-For-Race-Bryan-backend-hardening-v4.patch
git apply ~/Downloads/Hackathon-For-Race-Bryan-backend-hardening-v4.patch

uv run python -m compileall -q app scripts tests
node --check app/static/demo/app.js
uv run pytest -q
```

MySQL/RDS schema 尚未準備時，先在能連到資料庫的環境執行：

```bash
uv run python scripts/db_prepare.py
```

再重新部署：

```bash
source .cloud.env
uv run python scripts/cloud/preflight.py
scripts/cloud/deploy.sh
```
