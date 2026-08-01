# 🔑 資料庫連線快速參考卡

**最後更新**: 2026-08-01

---

## Amazon RDS MySQL

### 連線資訊
```
主機: smart-care-agent-db.c1e6cmcsyqsm.us-west-2.rds.amazonaws.com
埠號: 3306
資料庫: smart_care_agent
使用者: smart_care_app
密碼: Hackathon2026SecurePass!
```

### 連線字串
```
mysql://smart_care_app:Hackathon2026SecurePass!@smart-care-agent-db.c1e6cmcsyqsm.us-west-2.rds.amazonaws.com:3306/smart_care_agent
```

### 快速連線
```bash
# MySQL CLI
mysql -h smart-care-agent-db.c1e6cmcsyqsm.us-west-2.rds.amazonaws.com \
      -P 3306 -u smart_care_app -p smart_care_agent

# Prisma Studio
npx prisma studio

# 測試腳本
python scripts/test_rds_connection.py
```

---

## Amazon DynamoDB

### 區域
```
us-west-2
```

### 表格
- smart_care_residents
- smart_care_events
- smart_care_users
- smart_care_audit_log

### 快速測試
```bash
python scripts/dynamodb_example.py
```

---

## AWS 憑證

### 區域
```
us-west-2
```

### 帳號
```
564282910101
```

### 環境變數 (.env)
```bash
AWS_DEFAULT_REGION=us-west-2
AWS_ACCESS_KEY_ID=ASIAYGYPB4WK5XBCNZNX
AWS_SECRET_ACCESS_KEY=bdfUvts6LF+7XfWWYVPux9bmJuprhHJzd6q0JQWd
```

---

## 常用指令

### 查看 RDS 狀態
```bash
aws rds describe-db-instances --db-instance-identifier smart-care-agent-db
```

### 停止 RDS (節省成本)
```bash
aws rds stop-db-instance --db-instance-identifier smart-care-agent-db
```

### 啟動 RDS
```bash
aws rds start-db-instance --db-instance-identifier smart-care-agent-db
```

### 建立快照
```bash
aws rds create-db-snapshot \
  --db-instance-identifier smart-care-agent-db \
  --db-snapshot-identifier backup-$(date +%Y%m%d)
```

---

## 文件位置

- **完整工作記錄**: `docs/WorkRecord/2026-08-01-database-remote-deployment.md`
- **部署報告**: `docs/RDS_DEPLOYMENT_SUCCESS_REPORT.md`
- **連線資訊**: `rds_connection_info.json`
- **驗證報告**: `rds_verification_report.json`

---

## 緊急聯絡

**技術負責人**: [填寫]  
**AWS 帳號管理員**: [填寫]  

---

⚠️ **請勿將此文件提交至公開 repository**
