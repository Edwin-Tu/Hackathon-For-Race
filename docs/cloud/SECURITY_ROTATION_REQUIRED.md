# 必須完成的安全輪替

組員提供的雲端壓縮檔曾包含可用於 AWS／RDS 的明文連線資料。整合版已排除這些檔案，但刪除或排除檔案**不會**讓既有憑證自動失效。

## 必做

1. 在 AWS IAM、STS 提供來源或比賽憑證管理頁撤銷／輪替舊 Access Key、Secret Key、Session Token。
2. 修改 RDS Master User 與 App User 密碼。
3. 搜尋 GitHub、聊天附件、雲端硬碟及 Git history 中的舊值。
4. 若曾推送 Git，使用 `git filter-repo` 或 BFG 清理歷史；即使清理，也仍必須輪替憑證。
5. 移除 RDS Security Group 的 `0.0.0.0/0:3306`、`::/0:3306` 與不必要 CIDR。
6. 後續只透過 AWS Secrets Manager ARN 注入 ECS Task。
7. 更新 Secret 後對 ECS Service 執行 Force New Deployment，使新 Task 取得新值。
8. 檢查 CloudTrail、RDS Login／Audit 與異常資源建立紀錄。

## 不應提交

- `.env`、`.env.*`
- `rds_connection_info.json`
- `dynamodb_connection_info.json`
- AWS Access Key／Secret Key／Session Token
- 完整 `DATABASE_URL`
- API Bearer Token
- 私鑰、憑證或包含實際密碼的部署輸出

## 專案防線

部署前執行：

```bash
python3 scripts/cloud/secret_scan.py .
```

此掃描是最低限度的防呆，不能取代 GitHub Secret Scanning、AWS IAM Access Analyzer、CloudTrail 或人工稽核。
