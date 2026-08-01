# Config Directory

此目錄包含專案配置文件和連線資訊。

## 📁 檔案說明

| 檔案 | 說明 | 用途 |
|------|------|------|
| `dynamodb_connection_info.json` | DynamoDB 連線資訊 | 記錄 4 個 DynamoDB 表格的 ARN 和狀態 |
| `rds_connection_info.json` | RDS MySQL 連線資訊 | 記錄 RDS 實例的端點和配置 |
| `rds_verification_report.json` | RDS 驗證報告 | 資料庫部署驗證結果 |
| `opencode.json` | OpenCode AI 配置 | AI 助理的專案配置 |

## 🔒 安全性注意事項

⚠️ **重要**: 這些配置文件包含敏感資訊：

- ✅ 已加入 `.gitignore`（確保不會提交到 Git）
- ✅ 僅用於本地開發環境
- ⚠️ 生產環境應使用 AWS Secrets Manager 或環境變數
- ⚠️ 不要將這些文件分享給未授權人員

## 📊 DynamoDB 配置

`dynamodb_connection_info.json` 包含：

```json
{
  "tables": {
    "smart_care_residents": "arn:aws:dynamodb:...",
    "smart_care_events": "arn:aws:dynamodb:...",
    "smart_care_users": "arn:aws:dynamodb:...",
    "smart_care_audit_log": "arn:aws:dynamodb:..."
  }
}
```

## 🗄️ RDS 配置

`rds_connection_info.json` 包含：

```json
{
  "endpoint": "smart-care-agent-db.xxx.rds.amazonaws.com",
  "port": 3306,
  "database": "smart_care_agent",
  "region": "us-west-2"
}
```

## 🔗 相關環境變數

這些配置文件對應的環境變數（在 `.env` 中）：

```bash
# MySQL/RDS
DATABASE_URL="mysql://user:pass@endpoint:3306/database"

# DynamoDB
DYNAMODB_RESIDENTS_TABLE=smart_care_residents
DYNAMODB_EVENTS_TABLE=smart_care_events
DYNAMODB_USERS_TABLE=smart_care_users
DYNAMODB_AUDIT_TABLE=smart_care_audit_log

# AWS
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

## 📝 最佳實踐

1. **本地開發**: 使用這些 JSON 配置文件
2. **生產環境**: 使用環境變數或 AWS Secrets Manager
3. **團隊協作**: 不共享實際的連線資訊，使用範例檔案
4. **安全性**: 定期輪替資料庫密碼和 AWS 憑證

## 🔗 相關文檔

- [環境變數配置](.env.example)
- [資料庫連線快速參考](../docs/DATABASE_CONNECTION_QUICK_REFERENCE.md)
- [AWS 部署指南](../docs/AWS_DATABASE_DEPLOYMENT_GUIDE.md)
