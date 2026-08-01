# AWS 雲端資料庫部署指南

## AWS 憑證狀態

✅ **你的 AWS 憑證已驗證且可用！**

- **Account ID**: 564282910101
- **User ARN**: arn:aws:sts::564282910101:assumed-role/WSParticipantRole/Participant
- **Region**: us-west-2
- **IAM 權限**: 已確認有讀取權限

## 資料庫選項

我已為你準備了兩個部署腳本，你可以根據需求選擇：

### 選項 1: Amazon RDS MySQL（關聯式資料庫）

**優點:**
- 完全相容 MySQL，與現有的 `.env` 配置一致
- 支援標準 SQL 查詢
- 熟悉的關聯式資料庫模型
- 自動備份與還原

**缺點:**
- 成本較高（~$15-20/月）
- 需要持續運行（即使沒有流量）
- 需要 5-10 分鐘才能完成部署

**部署指令:**
```bash
python scripts/deploy_rds_mysql.py
```

**連線資訊:**
部署後會自動產生 `rds_connection_info.json`，包含連線字串可直接更新到 `.env`

---

### 選項 2: Amazon DynamoDB（NoSQL 無伺服器）

**優點:**
- **成本極低**（~$0-5/月，低流量下幾乎免費）
- 無伺服器架構，自動擴展
- 部署快速（< 1 分鐘）
- 按需計費，沒有流量時不收費
- 高可用性與耐久性

**缺點:**
- NoSQL 架構，需要調整應用程式邏輯
- 沒有 JOIN 查詢（需要在應用層處理）
- 學習曲線（如果不熟悉 NoSQL）

**部署指令:**
```bash
python scripts/deploy_dynamodb.py
```

**建立的表格:**
- `smart_care_residents` - 住民資料
- `smart_care_events` - 事件記錄
- `smart_care_users` - 使用者資料
- `smart_care_audit_log` - 審計日誌

---

## 建議

對於 **Hackathon 專案**，我強烈建議：

### 🎯 選擇 DynamoDB 的理由：
1. **成本效益**: 低流量下幾乎免費，對預算友善
2. **快速部署**: 1 分鐘內完成，可以立即開始開發
3. **無需維護**: 不用管理伺服器、備份等
4. **自動擴展**: 未來如果流量增加會自動處理

### 如果你需要 MySQL：
- 選擇 RDS MySQL，因為它與你現有的架構完全相容
- 可以直接使用現有的 SQL 查詢和 ORM
- 開發速度更快（不需要重寫資料存取層）

---

## 快速部署步驟

### 部署 DynamoDB（推薦）:
```bash
cd C:\Users\hc105\Hackathon-For-Race
python scripts/deploy_dynamodb.py
```

### 部署 RDS MySQL（如需傳統 SQL）:
```bash
cd C:\Users\hc105\Hackathon-For-Race
python scripts/deploy_rds_mysql.py
```

---

## 重要安全提醒

⚠️ **當前配置為開發環境設定**

部署腳本中的以下設定**僅適用於開發/測試**：

1. **PubliclyAccessible=True** - RDS 可從網際網路存取
2. **0.0.0.0/0** - 安全組允許所有 IP 連線
3. **DeletionProtection=False** - 未啟用刪除保護

**生產環境必須修改:**
- 限制安全組只允許特定 IP/VPC
- 啟用刪除保護
- 使用更強的密碼
- 啟用加密（RDS 已啟用，DynamoDB 預設啟用）

---

## 部署後的下一步

### 如果選擇 RDS MySQL:
1. 更新 `.env` 中的 `DATABASE_URL`
2. 執行資料庫遷移/初始化腳本
3. 測試連線

### 如果選擇 DynamoDB:
1. 安裝 boto3（已安裝）: `pip install boto3`
2. 實作 DynamoDB 資料存取層
3. 更新應用程式使用 DynamoDB SDK

---

## 刪除資源（避免持續收費）

### 刪除 RDS 實例:
```bash
aws rds delete-db-instance --db-instance-identifier smart-care-agent-db --skip-final-snapshot --region us-west-2
```

### 刪除 DynamoDB 表格:
```bash
aws dynamodb delete-table --table-name smart_care_residents --region us-west-2
aws dynamodb delete-table --table-name smart_care_events --region us-west-2
aws dynamodb delete-table --table-name smart_care_users --region us-west-2
aws dynamodb delete-table --table-name smart_care_audit_log --region us-west-2
```

---

## 成本比較

| 服務 | 月成本估算（低流量） | 優點 |
|------|---------------------|------|
| **RDS MySQL (db.t3.micro)** | ~$15-20 | 傳統 SQL，易於開發 |
| **DynamoDB (按需付費)** | ~$0-5 | 無伺服器，幾乎免費 |
| **本地 MySQL (127.0.0.1)** | $0 | 開發測試用 |

---

## 需要協助？

如果在部署過程中遇到問題，請告訴我：
- 錯誤訊息
- 你選擇的資料庫類型
- 遇到問題的步驟

我會協助你解決！
