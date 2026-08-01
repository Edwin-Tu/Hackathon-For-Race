# Scripts Directory

此目錄包含 Python 部署和自動化腳本。

## 📁 腳本清單

| 腳本 | 用途 | 說明 |
|------|------|------|
| `deploy_rds_mysql.py` | RDS 部署 | 部署 Amazon RDS MySQL 實例 |
| `deploy_dynamodb.py` | DynamoDB 部署 | 部署 4 個 DynamoDB 表格 |
| `deploy_rds_and_sync.py` | 完整部署 | RDS 部署 + Prisma Schema 同步 |
| `test_rds_connection.py` | 連線測試 | 測試 RDS 連線狀態 |
| `dynamodb_example.py` | 使用範例 | DynamoDB CRUD 操作範例 |

## 🚀 使用方式

### 前置要求

```bash
# 安裝 Python 依賴
cd tools/python
pip install -r requirements.txt

# 配置 AWS 憑證
# 方式 1: 環境變數
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-west-2

# 方式 2: .env 檔案
# 專案根目錄的 .env 檔案中配置
```

### 1. 部署 RDS MySQL

```bash
python scripts/deploy_rds_mysql.py
```

**功能**:
- 建立 RDS MySQL 8.0 實例
- 配置安全組
- 設定自動備份
- 返回連線資訊

**輸出**:
```json
{
  "endpoint": "smart-care-agent-db.xxx.rds.amazonaws.com",
  "port": 3306,
  "database": "smart_care_agent"
}
```

### 2. 部署 DynamoDB 表格

```bash
python scripts/deploy_dynamodb.py
```

**功能**:
- 建立 4 個 DynamoDB 表格
  - smart_care_residents
  - smart_care_events
  - smart_care_users
  - smart_care_audit_log
- 配置 GSI (Global Secondary Index)
- 設定計費模式（Pay-per-request）

### 3. 完整部署與同步

```bash
python scripts/deploy_rds_and_sync.py
```

**功能**:
- 部署 RDS MySQL 實例
- 等待實例可用
- 同步 Prisma Schema
- 執行資料庫遷移
- 驗證連線

**流程**:
```
1. 部署 RDS → 2. 等待可用 → 3. Prisma 同步 → 4. 驗證 → 完成
```

### 4. 測試 RDS 連線

```bash
python scripts/test_rds_connection.py
```

**檢查項目**:
- ✅ 連線成功
- ✅ 資料庫存在
- ✅ 表格建立
- ✅ 權限正確

### 5. DynamoDB 範例

```bash
python scripts/dynamodb_example.py
```

**範例操作**:
- 插入資料 (PutItem)
- 查詢資料 (GetItem)
- 掃描表格 (Scan)
- 更新資料 (UpdateItem)
- 刪除資料 (DeleteItem)

## 📝 腳本說明

### deploy_rds_mysql.py

**參數**:
```python
DB_INSTANCE_ID = "smart-care-agent-db"
DB_NAME = "smart_care_agent"
MASTER_USERNAME = "admin"
INSTANCE_CLASS = "db.t3.micro"
ALLOCATED_STORAGE = 20  # GB
```

**返回值**:
```python
{
    "success": True,
    "endpoint": "...",
    "port": 3306,
    "database": "smart_care_agent"
}
```

### deploy_dynamodb.py

**表格結構**:

#### smart_care_residents
```python
{
    "TableName": "smart_care_residents",
    "KeySchema": [
        {"AttributeName": "residentId", "KeyType": "HASH"}
    ],
    "AttributeDefinitions": [
        {"AttributeName": "residentId", "AttributeType": "S"}
    ]
}
```

#### smart_care_events
```python
{
    "TableName": "smart_care_events",
    "KeySchema": [
        {"AttributeName": "eventId", "KeyType": "HASH"},
        {"AttributeName": "timestamp", "KeyType": "RANGE"}
    ],
    "GlobalSecondaryIndexes": [
        {
            "IndexName": "ResidentIdIndex",
            "KeySchema": [
                {"AttributeName": "residentId", "KeyType": "HASH"}
            ]
        }
    ]
}
```

### deploy_rds_and_sync.py

**完整流程**:
```python
1. check_aws_credentials()       # 檢查 AWS 憑證
2. deploy_rds()                   # 部署 RDS
3. wait_for_rds_available()       # 等待實例可用
4. update_env_file()              # 更新 .env
5. run_prisma_sync()              # Prisma 同步
6. verify_connection()            # 驗證連線
```

## ⚠️ 注意事項

### 安全性

1. **AWS 憑證**
   - ⚠️ 不要將 AWS 憑證提交到 Git
   - ✅ 使用環境變數或 AWS CLI 配置
   - ✅ 定期輪替憑證

2. **資料庫密碼**
   - ⚠️ 不要硬編碼密碼
   - ✅ 使用 AWS Secrets Manager
   - ✅ 或從環境變數讀取

3. **網路安全**
   - ✅ RDS 安全組僅開放必要 IP
   - ✅ 使用 VPC 內部網路（生產環境）
   - ✅ 啟用 SSL/TLS 連線

### 成本考量

| 服務 | 配置 | 預估成本/月 |
|------|------|------------|
| RDS MySQL | db.t3.micro, 20GB | ~$15 |
| DynamoDB | Pay-per-request | ~$1-5 |
| **總計** | - | **~$16-20** |

### 最佳實踐

1. **開發環境**
   - 使用 docker-compose 本地開發
   - 避免直連雲端資料庫

2. **測試環境**
   - 使用獨立的 RDS 實例
   - 定期重置測試資料

3. **生產環境**
   - 啟用自動備份（7-30 天）
   - 配置 Multi-AZ（高可用）
   - 設定監控告警

## 🔧 故障排除

### 問題 1: AWS 憑證錯誤

```bash
# 檢查 AWS CLI 配置
aws sts get-caller-identity

# 檢查環境變數
echo $AWS_ACCESS_KEY_ID
echo $AWS_DEFAULT_REGION
```

### 問題 2: RDS 部署失敗

```python
# 檢查日誌
python scripts/deploy_rds_mysql.py --verbose

# 檢查現有實例
aws rds describe-db-instances --db-instance-identifier smart-care-agent-db
```

### 問題 3: Prisma 同步失敗

```bash
# 手動同步
npx prisma db push

# 重新生成 Client
npx prisma generate
```

### 問題 4: DynamoDB 表格已存在

```python
# 刪除現有表格（⚠️ 危險操作）
aws dynamodb delete-table --table-name smart_care_residents

# 等待刪除完成
aws dynamodb wait table-not-exists --table-name smart_care_residents
```

## 📊 監控與日誌

### CloudWatch 監控

```python
# 查看 RDS 指標
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=smart-care-agent-db
```

### 腳本日誌

腳本會產生日誌文件：
```
logs/
├── deploy_rds_YYYYMMDD_HHMMSS.log
├── deploy_dynamodb_YYYYMMDD_HHMMSS.log
└── test_connection_YYYYMMDD_HHMMSS.log
```

## 🔗 相關資源

- [AWS RDS 文檔](https://docs.aws.amazon.com/rds/)
- [AWS DynamoDB 文檔](https://docs.aws.amazon.com/dynamodb/)
- [Boto3 文檔](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Prisma 文檔](https://www.prisma.io/docs)

## 📞 支援

遇到問題？
1. 檢查 [故障排除](#故障排除) 章節
2. 查看 [專案文檔](../docs/)
3. 提交 [GitHub Issue](https://github.com/Edwin-Tu/Hackathon-For-Race/issues)

---

**最後更新**: 2026-08-01  
**維護者**: DevOps 團隊
