#!/bin/bash
# deploy.sh - AWS SAM 部署腳本
# 使用方式: ./deploy.sh [dev|prod]

set -e

ENVIRONMENT=${1:-prod}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "================================================"
echo "  AI Video Generator - AWS 部署"
echo "  環境: $ENVIRONMENT"
echo "================================================"

# 檢查 AWS CLI
if ! command -v aws &> /dev/null; then
    echo "錯誤: 請先安裝 AWS CLI"
    exit 1
fi

# 檢查 SAM CLI
if ! command -v sam &> /dev/null; then
    echo "錯誤: 請先安裝 AWS SAM CLI"
    echo "安裝指南: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
fi

# 檢查 AWS 認證
echo ""
echo "步驟 1: 檢查 AWS 認證..."
aws sts get-caller-identity > /dev/null 2>&1 || {
    echo "錯誤: AWS 認證失敗，請確認 AWS_ACCESS_KEY_ID 和 AWS_SECRET_ACCESS_KEY"
    exit 1
}
echo "✓ AWS 認證成功"

# 進入 infra 目錄
cd "$SCRIPT_DIR"

# 安裝 Lambda 依賴
echo ""
echo "步驟 2: 安裝 Lambda 依賴..."
cd ../lambda/generate-video
npm install --production
cd "$SCRIPT_DIR"
echo "✓ Lambda 依賴安裝完成"

# 驗證 SAM 模板
echo ""
echo "步驟 3: 驗證 SAM 模板..."
sam validate --template template.yaml
echo "✓ SAM 模板驗證通過"

# 建置
echo ""
echo "步驟 4: 建置 SAM 應用..."
sam build --template template.yaml
echo "✓ 建置完成"

# 部署
echo ""
echo "步驟 5: 部署到 AWS ($ENVIRONMENT)..."
if [ "$ENVIRONMENT" = "dev" ]; then
    sam deploy --config-env dev --no-confirm-changeset
else
    sam deploy --config-env prod
fi

echo ""
echo "================================================"
echo "  部署完成！"
echo "================================================"
echo ""
echo "請更新 .env.local 中的以下變數："
echo ""

# 取得 Stack Outputs
STACK_NAME="hackathon-video-$ENVIRONMENT"
echo "AWS_S3_IMAGES_BUCKET=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`ImagesBucketName`].OutputValue' --output text)"
echo "AWS_S3_VIDEOS_BUCKET=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`VideosBucketName`].OutputValue' --output text)"
echo "AWS_DYNAMODB_TABLE_VIDEO_TASKS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`VideoTasksTableName`].OutputValue' --output text)"
