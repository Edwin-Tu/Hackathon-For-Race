# Cloud Integration Report

## 結論

已將目前穩定的：

```text
Input Guard + Skill + Bedrock Agent + Tool Gateway + Confirmation Resume
+ MySQL + Whisper + Reminder Scheduler + Validation UI
```

整合為可部署到 AWS 的 Cloud-Ready 版本。主要部署目標為：

```text
API Gateway HTTP API (HTTPS)
→ VPC Link
→ Internal ALB
→ ECS Fargate
→ RDS MySQL / Bedrock Runtime
```

組員 Edwin 的 RDS 成果被保留為雲端資料庫目標，但沒有把壓縮檔內的明文 AWS／RDS 憑證、公開 MySQL 規則、基礎 Bedrock Client 或不相容 Middleware 複製進正式執行鏈。

## 主要修正

### Database Adapter

- `CARE_EVENT_TABLE=auto`
- 自動支援 `events` 與 `care_events`
- 動態偵測 `reminders` 欄位
- 全部資料值使用 parameterized SQL
- 資料表識別字固定 allowlist
- RDS TLS `verify_identity`
- RDS global CA bundle

### Cloud Runtime

- Dockerfile：Python 3.12、ffmpeg、Whisper small 預載、非 root user
- ECS Fargate：2 vCPU／4 GB、單 Task／單 Worker
- Internal ALB：不直接公開 ECS
- API Gateway：提供 HTTPS 與 VPC Link private integration
- Secrets Manager：注入 `DATABASE_URL`、`API_BEARER_TOKEN`
- ECR、Logs、Secrets Manager、Bedrock Runtime Interface Endpoint
- S3 Gateway Endpoint
- RDS Security Group 僅允許 ECS Task SG

### Public Demo Protection

- `/api/*` Bearer Token 驗證
- `/health` 與 `/demo` 保留公開
- constant-time token comparison
- CSP、X-Frame-Options、nosniff、Referrer-Policy
- Browser Validation UI 可輸入 Token
- Browser microphone + Browser TTS
- 雲端容器不呼叫 macOS `say`／`afplay`

### Secret Hygiene

- 新增 Secret Scanner
- `.dockerignore`／`.gitignore` 排除 credentials、connection-info、音訊與壓縮檔
- Secrets 建立／更新腳本不將值輸出至 Console
- 提供 RDS 公開 3306 移除腳本
- 明確要求輪替組員壓縮檔曾出現的憑證

### Deployment

- `scripts/cloud/deploy.sh`：主要入口，部署 ECS Fargate
- `scripts/cloud/deploy_ecs.sh`：ECR build/push + Secrets + CloudFormation
- `infra/ecs/stack.yaml`：27 個 CloudFormation resources
- `scripts/cloud/preflight.py`：AWS、Docker、STS、VPC、Subnet、Route Table、RDS URL、Token 驗證
- `scripts/cloud/smoke_cloud.py`：Health、Input Guard、可選 Bedrock Agent Smoke Test
- App Runner 路徑標記為 legacy-only，需顯式 opt-in

## 驗證結果

```text
129 passed in 5.98s
```

另外完成：

- Python `compileall`：PASS
- JavaScript syntax check：PASS
- 所有 Cloud Shell script `bash -n`：PASS
- Secret Scan：PASS
- ECS CloudFormation YAML parse：PASS（27 resources）
- Legacy App Runner YAML parse：PASS（9 resources）
- Python wheel build：PASS

## 未在本環境執行

本建置環境沒有 Docker daemon、AWS CLI、你的 AWS Credentials、VPC、RDS 與 Bedrock 存取，因此以下仍需在你的 Mac／比賽 AWS 帳號實際執行：

- Docker image build
- ECR push
- CloudFormation validation/deployment
- ECS Task startup
- API Gateway VPC Link 建立
- RDS TLS 真實連線
- Bedrock 真實雲端呼叫
- Browser microphone HTTPS 實機測試

因此本成果是「程式、IaC 與靜態／單元測試已完成」，不是宣稱 AWS Resource 已經實際部署成功。

## 部署入口

完整步驟見：

```text
docs/cloud/CLOUD_DEPLOYMENT.md
```

主要指令：

```bash
python3 scripts/cloud/secret_scan.py .
python3 scripts/cloud/preflight.py
scripts/cloud/deploy.sh
```
