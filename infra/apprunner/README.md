# Legacy App Runner deployment

AWS App Runner 已停止接受新客戶；此目錄只保留給在截止日前已使用 App Runner 的 AWS 帳號。

新部署請使用：

```bash
scripts/cloud/deploy.sh
```

它會部署至 ECS Fargate + API Gateway。若帳號確定是既有 App Runner 客戶，必須明確設定：

```bash
export ALLOW_LEGACY_APPRUNNER=true
scripts/cloud/deploy_apprunner.sh
```
