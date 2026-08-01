# deploy.ps1 - AWS SAM 部署腳本 (Windows PowerShell)
# 使用方式: .\deploy.ps1 [-Environment dev|prod]

param(
    [ValidateSet("dev", "prod")]
    [string]$Environment = "prod"
)

$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI Video Generator - AWS 部署" -ForegroundColor Cyan
Write-Host "  環境: $Environment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# 檢查 AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "錯誤: 請先安裝 AWS CLI" -ForegroundColor Red
    exit 1
}

# 檢查 SAM CLI
if (-not (Get-Command sam -ErrorAction SilentlyContinue)) {
    Write-Host "錯誤: 請先安裝 AWS SAM CLI" -ForegroundColor Red
    Write-Host "安裝指南: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
}

# 檢查 AWS 認證
Write-Host "`n步驟 1: 檢查 AWS 認證..." -ForegroundColor Yellow
try {
    aws sts get-caller-identity | Out-Null
    Write-Host "✓ AWS 認證成功" -ForegroundColor Green
} catch {
    Write-Host "錯誤: AWS 認證失敗，請確認 AWS_ACCESS_KEY_ID 和 AWS_SECRET_ACCESS_KEY" -ForegroundColor Red
    exit 1
}

# 取得腳本目錄
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# 安裝 Lambda 依賴
Write-Host "`n步驟 2: 安裝 Lambda 依賴..." -ForegroundColor Yellow
Push-Location ..\lambda\generate-video
npm install --production
Pop-Location
Write-Host "✓ Lambda 依賴安裝完成" -ForegroundColor Green

# 驗證 SAM 模板
Write-Host "`n步驟 3: 驗證 SAM 模板..." -ForegroundColor Yellow
sam validate --template template.yaml
if ($LASTEXITCODE -ne 0) {
    Write-Host "錯誤: SAM 模板驗證失敗" -ForegroundColor Red
    exit 1
}
Write-Host "✓ SAM 模板驗證通過" -ForegroundColor Green

# 建置
Write-Host "`n步驟 4: 建置 SAM 應用..." -ForegroundColor Yellow
sam build --template template.yaml
if ($LASTEXITCODE -ne 0) {
    Write-Host "錯誤: 建置失敗" -ForegroundColor Red
    exit 1
}
Write-Host "✓ 建置完成" -ForegroundColor Green

# 部署
Write-Host "`n步驟 5: 部署到 AWS ($Environment)..." -ForegroundColor Yellow
if ($Environment -eq "dev") {
    sam deploy --config-env dev --no-confirm-changeset
} else {
    sam deploy --config-env prod
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "錯誤: 部署失敗" -ForegroundColor Red
    exit 1
}

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "  部署完成！" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# 取得 Stack Outputs
$StackName = "hackathon-video-$Environment"

Write-Host "`n請更新 .env.local 中的以下變數：" -ForegroundColor Yellow
Write-Host ""

$ImagesBucket = aws cloudformation describe-stacks --stack-name $StackName --query 'Stacks[0].Outputs[?OutputKey==`ImagesBucketName`].OutputValue' --output text
$VideosBucket = aws cloudformation describe-stacks --stack-name $StackName --query 'Stacks[0].Outputs[?OutputKey==`VideosBucketName`].OutputValue' --output text
$DynamoTable = aws cloudformation describe-stacks --stack-name $StackName --query 'Stacks[0].Outputs[?OutputKey==`VideoTasksTableName`].OutputValue' --output text

Write-Host "AWS_S3_IMAGES_BUCKET=$ImagesBucket" -ForegroundColor White
Write-Host "AWS_S3_VIDEOS_BUCKET=$VideosBucket" -ForegroundColor White
Write-Host "AWS_DYNAMODB_TABLE_VIDEO_TASKS=$DynamoTable" -ForegroundColor White
