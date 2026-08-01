# Edwin 雲端成果整合說明

## 整合策略

組員完成的核心成果是 Amazon RDS MySQL、Prisma Migration 與雲端資源部署。本整合版保留你的安全 Agent 主線，再以 Database Adapter 連接組員 RDS：

```text
Input Guard → Skill → Bedrock Claude → Tool Gateway
             → Adaptive MySQL/RDS Repository → Edwin RDS
```

## 已整合

- 保留 Edwin RDS 作為雲端持久化目標。
- Adapter 自動偵測：
  - 本機 `events`
  - Edwin RDS `care_events`
- Adapter 依 `information_schema` 判斷 `reminders` 實際欄位，避免兩版 Schema 差異造成 INSERT 失敗。
- RDS TLS hostname/CA 驗證。
- ECS Fargate + Internal ALB + API Gateway HTTPS 部署範本。
- Secrets Manager 注入 `DATABASE_URL` 與 API Token。
- Bedrock Runtime、ECR、Logs、Secrets Manager 私有 VPC Endpoint 選項。
- idempotent Demo Persona/User Seed。
- RDS Security Group 只允許 ECS Task Security Group 連入 3306。

## 未合併

以下內容不會直接複製進正式專案：

- 明文 AWS／RDS 憑證或 connection-info JSON。
- 基礎 `bedrock_client.py`；現有 Bedrock Converse Tool Use Provider 更完整。
- 未與 Prisma Schema 對齊的 `authorization.ts` 草案。
- 尚未被 Agent 使用的 DynamoDB 表。
- 以文件宣稱但沒有可執行證據的前端／多租戶功能。
- 公開 `0.0.0.0/0:3306` 網路設定。

## 為何不直接改名資料表

Edwin RDS 使用 `care_events`，本機已驗證環境使用 `events`。直接 Rename 可能影響 `event_revisions` 外鍵、Prisma Migration 與其他組員程式。比賽前採用相容 Adapter，避免破壞性 Schema Migration。

比賽後應決定唯一 Canonical Schema，再以正式 Migration 收斂，不應長期維護兩套資料表名稱。

## DynamoDB 決策

目前不把 `smart_care_events` DynamoDB 表接成第二套事件儲存，避免 MySQL 與 DynamoDB 同時成為 Source of Truth。後續可將 DynamoDB 用於：

- Process-independent Confirmation Store
- Output Event／WebSocket Delivery Buffer
- Session Risk Tracker

但需要獨立一致性與 TTL 設計後再接入。
