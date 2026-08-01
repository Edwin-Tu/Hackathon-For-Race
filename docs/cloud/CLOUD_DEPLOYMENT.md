# AWS 雲端部署指南

## 部署目標

本專案的主要雲端部署目標是 **Amazon ECS on AWS Fargate**：

```text
Browser Validation UI / microphone (HTTPS)
        ↓
Amazon API Gateway HTTP API
        ↓ VPC Link
Internal Application Load Balancer
        ↓
Amazon ECS Fargate (FastAPI, Input Guard, Skill, Claude Agent,
                    Tool Gateway, Whisper, Reminder Scheduler)
        ├── private VPC → Amazon RDS MySQL
        ├── VPC endpoint → Amazon Bedrock Runtime
        ├── VPC endpoints → ECR / CloudWatch Logs / Secrets Manager
        └── Secrets Manager → DATABASE_URL / API_BEARER_TOKEN
```

API Gateway 提供公開 HTTPS 端點；ECS Task、ALB 與 RDS 留在 VPC 私有網路。驗證 UI 使用瀏覽器錄音與瀏覽器 TTS，因此雲端容器不依賴 macOS `say` 或實體音訊裝置。

> `infra/apprunner/` 只保留給既有 App Runner 客戶作相容參考。新的部署一律使用 ECS Fargate。

## 已處理的 Edwin 專案差異

- 不匯入任何明文 AWS Key、RDS 密碼或 connection-info JSON。
- `CARE_EVENT_TABLE=auto` 可偵測本機 `events` 或 Edwin RDS `care_events`。
- `reminders` 依 `information_schema` 偵測可用欄位，支援兩版 Schema。
- 不執行破壞性的 `prisma db push`，避免改壞既有 RDS Migration。
- RDS 連線採 TLS `verify_identity` 與 AWS RDS global CA bundle。
- Demo Persona/User Seed 為 idempotent。

## 0. 部署前必做安全處理

1. **立即輪替**組員壓縮檔中曾出現的 AWS Access Key、Secret Key／Session Token 與 RDS 密碼。
2. 檢查 GitHub、聊天附件與 Git history；只刪除目前檔案不會讓舊憑證失效。
3. RDS Security Group 不得保留 `0.0.0.0/0:3306`。
4. 建議建立只具 `SELECT/INSERT/UPDATE` 必要權限的 MySQL App User。
5. 不要把 `DATABASE_URL` 或 API Token 寫入 Git、README、CloudFormation Parameter plaintext 或 Shell script。

詳見 `docs/cloud/SECURITY_ROTATION_REQUIRED.md`。

## 1. 本機驗證 Cloud-Compatible Adapter

```bash
cp .env.example .env
uv sync --extra voice
uv run pytest -q
uv run python -m scripts.db_integration_check
```

確認：

- 本機 `events` 或 RDS `care_events` 可自動偵測。
- Reminder 建立、確認續接、到點 claim 與狀態更新正常。
- Input Guard BLOCK 時不呼叫 Bedrock、不執行工具、不寫入資料庫。

## 2. 準備 AWS 與網路資訊

需要既有 RDS 所在 VPC 的：

- VPC ID
- 至少兩個 Private Subnet ID（不同 AZ）
- 這些 Private Subnet 對應的 Route Table ID
- RDS Security Group ID

設定部署變數：

```bash
export AWS_REGION=us-west-2
export VPC_ID=vpc-xxxxxxxx
export PRIVATE_SUBNET_IDS=subnet-aaa,subnet-bbb
export PRIVATE_ROUTE_TABLE_IDS=rtb-aaa,rtb-bbb
export RDS_SECURITY_GROUP_ID=sg-xxxxxxxx

export DEMO_USER_ID=c638fd87-4af2-4813-af34-c9694f94d946
export DEMO_PERSONA_ID=a1000000-0000-0000-0000-000000000001

# 密碼含 @ : / # % 時，密碼段必須 URL encode。
export DATABASE_URL='mysql://smart_care_app:ENCODED_PASSWORD@RDS_ENDPOINT:3306/smart_care_agent'
export API_BEARER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

建議以不回顯方式輸入敏感值，避免留下 Shell history：

```bash
read -s -p 'DATABASE_URL: ' DATABASE_URL; echo
export DATABASE_URL
read -s -p 'API_BEARER_TOKEN: ' API_BEARER_TOKEN; echo
export API_BEARER_TOKEN
```

### 私有子網路是否已有 NAT

預設：

```bash
export CREATE_PRIVATE_ENDPOINTS=true
```

CloudFormation 會建立 ECR API、ECR DKR、CloudWatch Logs、Secrets Manager、Bedrock Runtime 的 Interface Endpoint，以及 S3 Gateway Endpoint。

若 VPC 已有等價 Endpoint，或 Private Subnet 已可透過 NAT 存取 AWS 服務，可設定：

```bash
export CREATE_PRIVATE_ENDPOINTS=false
```

避免建立重複 Endpoint。

## 3. Seed RDS Demo 身分

在可安全連入 RDS 的機器執行：

```bash
export DATABASE_SSL_MODE=verify_identity
export DATABASE_SSL_CA=/path/to/global-bundle.pem
python3 -m scripts.cloud.seed_demo
```

這會 idempotently 建立／更新：

- 王奶奶 Persona
- Resident App User
- 自己 Persona 的存取關係

不會輸出密碼或完整連線字串。

## 4. Preflight

```bash
python3 scripts/cloud/secret_scan.py .
python3 scripts/cloud/preflight.py
```

Preflight 會檢查：

- 專案中是否可能殘留 AWS Key、Private Key 或含真密碼的 MySQL URL
- `aws` 與 `docker` 是否存在
- AWS STS 憑證是否有效
- VPC、Subnet、Route Table、RDS SG、Demo ID 是否設定

## 5. 部署 ECS Fargate

```bash
scripts/cloud/deploy.sh
```

等同：

```bash
scripts/cloud/deploy_ecs.sh
```

腳本會：

1. 執行 Secret Scan。
2. 建立／沿用 ECR Repository，開啟 Push Scan。
3. 建置 `linux/amd64` 容器，預載 faster-whisper small 與 RDS CA bundle。
4. 推送映像到 ECR。
5. 將 `DATABASE_URL`、`API_BEARER_TOKEN` 寫入 Secrets Manager。
6. 部署 ECS Fargate、Internal ALB、API Gateway HTTP API、VPC Link、IAM、Security Group 與必要 VPC Endpoint。
7. 回傳公開 HTTPS URL。

目前服務固定：

```text
DesiredCount = 1
uvicorn workers = 1
```

原因是 Confirmation Store 與 Output Event Store 目前仍在單一 Process Memory 中。要水平擴充前，應先將它們遷移到 Redis／DynamoDB／RDS。

## 6. 移除 RDS 公開 3306

確認 ECS Task 已成功連線 RDS 後執行：

```bash
scripts/cloud/harden_rds_security_group.sh "$RDS_SECURITY_GROUP_ID"
```

此腳本只移除 `0.0.0.0/0:3306`；CloudFormation 加入的 ECS Task Security Group ingress 會保留。

也請人工確認沒有：

- `::/0:3306`
- 不必要的大範圍 IPv4/IPv6 CIDR
- 舊開發機 IP 長期保留

## 7. 雲端 Smoke Test

部署輸出會提供 `ServiceUrl`。設定：

```bash
export BASE_URL='https://xxxxxxxx.execute-api.us-west-2.amazonaws.com'
python3 scripts/cloud/smoke_cloud.py
python3 scripts/cloud/smoke_cloud.py --full-agent
# 會新增一筆測試事件，用於驗證 Agent → Tool Gateway → RDS
python3 scripts/cloud/smoke_cloud.py --write-event
```

驗證 UI：

```text
https://你的-ServiceUrl/demo
```

將 `API_BEARER_TOKEN` 貼進 UI 的 `Cloud API Token` 欄位。Token 只保存於該瀏覽器分頁的 `sessionStorage`。

## 8. 雲端驗收條件

### Input Guard BLOCK

- `allowed=false`
- Bedrock token usage = 0
- `tool_events=[]`
- `operation_completed=false`
- RDS `care_events/events`、`reminders` 筆數不增加

### Voice Agent ALLOW

- Whisper transcript 正確
- Input Guard ALLOW
- Claude 選擇正確工具
- Tool Gateway `status=succeeded`
- `record_id` 非空且 RDS 可查到相同 ID
- Browser TTS 可播報回覆

### Reminder Confirmation

- 第一輪 `requires_confirmation=true`
- 第二輪相同 session + token 直接執行凍結 ToolCall
- 確認回合 Bedrock token usage = 0
- `reminders` 產生真實 `record_id`
- 到點後 `scheduled → triggering → triggered`

## 目前限制

- 外部 API 目前使用 Demo Bearer Token，不是 Cognito/JWT。
- API Gateway HTTP API integration timeout 為 30 秒；Demo 音訊應保持短句，並已在映像中預載 Whisper 模型。
- API 音訊上限配置為 8 MiB，低於 API Gateway payload 上限。
- Reminder UI Event Buffer 與 Confirmation Store 在 Process Memory，服務重啟會遺失尚未完成的確認／UI 事件。
- Secrets Manager Secret 輪替後，ECS Task 不會自動取得新值；需重新部署或 Force New Deployment。
- 本範本不會建立 RDS 本身，只安全連接組員已建立的 RDS。

## 清理雲端資源

```bash
aws cloudformation delete-stack \
  --region "$AWS_REGION" \
  --stack-name "${STACK_NAME:-smart-care-agent-ecs}"
```

ECR Repository 與 Secrets Manager Secret 是由部署腳本在 Stack 外建立，需確認後另行刪除，避免誤刪仍使用中的資料或密碼。
