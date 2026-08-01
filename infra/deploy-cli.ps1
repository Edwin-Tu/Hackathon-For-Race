# deploy-cli.ps1 - 使用 AWS CLI 直接部署（不需要 SAM CLI）
# 使用方式: .\deploy-cli.ps1

$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI Video Generator - AWS 部署 (CLI 版本)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# 設定
$Region = "us-west-2"
$ProjectName = "my-app"
$ImagesBucket = "$ProjectName-images-prod-$Region"
$VideosBucket = "$ProjectName-videos-prod-$Region"
$TableName = "VideoTasks"
$LambdaName = "$ProjectName-generate-video"
$LambdaRoleName = "$ProjectName-lambda-role"

# 檢查 AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "錯誤: 請先安裝 AWS CLI" -ForegroundColor Red
    exit 1
}

# 檢查 AWS 認證
Write-Host "`n步驟 1: 檢查 AWS 認證..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
    Write-Host "✓ AWS 認證成功 (Account: $($identity.Account))" -ForegroundColor Green
} catch {
    Write-Host "錯誤: AWS 認證失敗" -ForegroundColor Red
    exit 1
}

$AccountId = $identity.Account

# ========================================
# 步驟 2: 建立 DynamoDB Table (如果不存在)
# ========================================
Write-Host "`n步驟 2: 檢查/建立 DynamoDB Table..." -ForegroundColor Yellow

$tableExists = $false
try {
    aws dynamodb describe-table --table-name $TableName --region $Region 2>$null | Out-Null
    $tableExists = $true
    Write-Host "✓ DynamoDB Table '$TableName' 已存在" -ForegroundColor Green
} catch {
    Write-Host "建立 DynamoDB Table..." -ForegroundColor White
}

if (-not $tableExists) {
    aws dynamodb create-table `
        --table-name $TableName `
        --attribute-definitions `
            AttributeName=taskId,AttributeType=S `
            AttributeName=residentId,AttributeType=S `
            AttributeName=createdAt,AttributeType=N `
        --key-schema AttributeName=taskId,KeyType=HASH `
        --billing-mode PAY_PER_REQUEST `
        --global-secondary-indexes '[{
            "IndexName": "residentId-createdAt-index",
            "KeySchema": [
                {"AttributeName": "residentId", "KeyType": "HASH"},
                {"AttributeName": "createdAt", "KeyType": "RANGE"}
            ],
            "Projection": {"ProjectionType": "ALL"}
        }]' `
        --region $Region

    Write-Host "等待 Table 建立完成..." -ForegroundColor White
    aws dynamodb wait table-exists --table-name $TableName --region $Region
    Write-Host "✓ DynamoDB Table 建立完成" -ForegroundColor Green
}

# ========================================
# 步驟 3: 設定 S3 CORS (如果 Bucket 存在)
# ========================================
Write-Host "`n步驟 3: 設定 S3 CORS..." -ForegroundColor Yellow

$corsConfig = @'
{
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "PUT", "POST"],
            "AllowedOrigins": ["*"],
            "MaxAgeSeconds": 3000
        }
    ]
}
'@

# 檢查 Images Bucket
try {
    aws s3api head-bucket --bucket $ImagesBucket --region $Region 2>$null
    Write-Host "✓ Images Bucket '$ImagesBucket' 存在，設定 CORS..." -ForegroundColor Green
    $corsConfig | aws s3api put-bucket-cors --bucket $ImagesBucket --cors-configuration file:///dev/stdin --region $Region 2>$null
} catch {
    Write-Host "⚠ Images Bucket '$ImagesBucket' 不存在，請先在 AWS Console 建立" -ForegroundColor Yellow
}

# 檢查 Videos Bucket
try {
    aws s3api head-bucket --bucket $VideosBucket --region $Region 2>$null
    Write-Host "✓ Videos Bucket '$VideosBucket' 存在" -ForegroundColor Green
} catch {
    Write-Host "⚠ Videos Bucket '$VideosBucket' 不存在，請先在 AWS Console 建立" -ForegroundColor Yellow
}

# ========================================
# 步驟 4: 建立 Lambda IAM Role
# ========================================
Write-Host "`n步驟 4: 檢查/建立 Lambda IAM Role..." -ForegroundColor Yellow

$roleExists = $false
try {
    aws iam get-role --role-name $LambdaRoleName 2>$null | Out-Null
    $roleExists = $true
    Write-Host "✓ IAM Role '$LambdaRoleName' 已存在" -ForegroundColor Green
} catch {
    Write-Host "建立 IAM Role..." -ForegroundColor White
}

if (-not $roleExists) {
    $trustPolicy = @'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
'@
    $trustPolicy | Set-Content -Path "$env:TEMP\trust-policy.json"
    
    aws iam create-role `
        --role-name $LambdaRoleName `
        --assume-role-policy-document "file://$env:TEMP\trust-policy.json"

    # 附加基本執行權限
    aws iam attach-role-policy `
        --role-name $LambdaRoleName `
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

    # 建立自定義權限
    $customPolicy = @"
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:PutObject"],
            "Resource": [
                "arn:aws:s3:::$ImagesBucket/*",
                "arn:aws:s3:::$VideosBucket/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:Query"
            ],
            "Resource": [
                "arn:aws:dynamodb:${Region}:${AccountId}:table/$TableName",
                "arn:aws:dynamodb:${Region}:${AccountId}:table/$TableName/index/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:StartAsyncInvoke",
                "bedrock:GetAsyncInvoke"
            ],
            "Resource": "*"
        }
    ]
}
"@
    $customPolicy | Set-Content -Path "$env:TEMP\custom-policy.json"
    
    aws iam put-role-policy `
        --role-name $LambdaRoleName `
        --policy-name "${LambdaName}-policy" `
        --policy-document "file://$env:TEMP\custom-policy.json"

    Write-Host "等待 Role 可用..." -ForegroundColor White
    Start-Sleep -Seconds 10
    Write-Host "✓ IAM Role 建立完成" -ForegroundColor Green
}

$LambdaRoleArn = "arn:aws:iam::${AccountId}:role/$LambdaRoleName"

# ========================================
# 步驟 5: 打包並部署 Lambda
# ========================================
Write-Host "`n步驟 5: 打包並部署 Lambda..." -ForegroundColor Yellow

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LambdaDir = Join-Path $ScriptDir "..\lambda\generate-video"
$ZipPath = Join-Path $env:TEMP "generate-video.zip"

# 安裝依賴
Push-Location $LambdaDir
npm install --production
Pop-Location

# 建立 ZIP
if (Test-Path $ZipPath) { Remove-Item $ZipPath }
Compress-Archive -Path "$LambdaDir\*" -DestinationPath $ZipPath -Force
Write-Host "✓ Lambda 打包完成" -ForegroundColor Green

# 檢查 Lambda 是否存在
$lambdaExists = $false
try {
    aws lambda get-function --function-name $LambdaName --region $Region 2>$null | Out-Null
    $lambdaExists = $true
} catch {}

if ($lambdaExists) {
    Write-Host "更新 Lambda 函式..." -ForegroundColor White
    aws lambda update-function-code `
        --function-name $LambdaName `
        --zip-file "fileb://$ZipPath" `
        --region $Region | Out-Null
    
    aws lambda update-function-configuration `
        --function-name $LambdaName `
        --timeout 300 `
        --memory-size 512 `
        --environment "Variables={AWS_S3_IMAGES_BUCKET=$ImagesBucket,AWS_S3_VIDEOS_BUCKET=$VideosBucket,AWS_DYNAMODB_TABLE_VIDEO_TASKS=$TableName,AWS_BEDROCK_MODEL_ID=luma.ray-v2:0}" `
        --region $Region | Out-Null
} else {
    Write-Host "建立 Lambda 函式..." -ForegroundColor White
    aws lambda create-function `
        --function-name $LambdaName `
        --runtime nodejs20.x `
        --role $LambdaRoleArn `
        --handler index.handler `
        --zip-file "fileb://$ZipPath" `
        --timeout 300 `
        --memory-size 512 `
        --environment "Variables={AWS_S3_IMAGES_BUCKET=$ImagesBucket,AWS_S3_VIDEOS_BUCKET=$VideosBucket,AWS_DYNAMODB_TABLE_VIDEO_TASKS=$TableName,AWS_BEDROCK_MODEL_ID=luma.ray-v2:0}" `
        --region $Region | Out-Null
}

Write-Host "✓ Lambda 部署完成" -ForegroundColor Green

# ========================================
# 步驟 6: 設定 S3 Event 觸發 Lambda
# ========================================
Write-Host "`n步驟 6: 設定 S3 Event 觸發..." -ForegroundColor Yellow

$LambdaArn = "arn:aws:lambda:${Region}:${AccountId}:function:$LambdaName"

# 允許 S3 呼叫 Lambda
try {
    aws lambda add-permission `
        --function-name $LambdaName `
        --statement-id "s3-trigger" `
        --action "lambda:InvokeFunction" `
        --principal s3.amazonaws.com `
        --source-arn "arn:aws:s3:::$ImagesBucket" `
        --region $Region 2>$null | Out-Null
} catch {
    # 權限可能已存在
}

# 設定 S3 通知
$notificationConfig = @"
{
    "LambdaFunctionConfigurations": [
        {
            "LambdaFunctionArn": "$LambdaArn",
            "Events": ["s3:ObjectCreated:*"],
            "Filter": {
                "Key": {
                    "FilterRules": [
                        {
                            "Name": "prefix",
                            "Value": "images/"
                        }
                    ]
                }
            }
        }
    ]
}
"@

try {
    $notificationConfig | Set-Content -Path "$env:TEMP\notification.json"
    aws s3api put-bucket-notification-configuration `
        --bucket $ImagesBucket `
        --notification-configuration "file://$env:TEMP\notification.json" `
        --region $Region
    Write-Host "✓ S3 Event 觸發設定完成" -ForegroundColor Green
} catch {
    Write-Host "⚠ S3 Event 設定失敗，請手動在 AWS Console 設定" -ForegroundColor Yellow
}

# ========================================
# 完成
# ========================================
Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "  部署完成！" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "已建立的資源：" -ForegroundColor White
Write-Host "  - DynamoDB Table: $TableName" -ForegroundColor Gray
Write-Host "  - IAM Role: $LambdaRoleName" -ForegroundColor Gray
Write-Host "  - Lambda: $LambdaName" -ForegroundColor Gray
Write-Host ""
Write-Host "請確認 .env.local 設定：" -ForegroundColor Yellow
Write-Host "  AWS_S3_IMAGES_BUCKET=$ImagesBucket"
Write-Host "  AWS_S3_VIDEOS_BUCKET=$VideosBucket"
Write-Host "  AWS_DYNAMODB_TABLE_VIDEO_TASKS=$TableName"
Write-Host ""
Write-Host "注意事項：" -ForegroundColor Yellow
Write-Host "  1. 請確認 Bedrock luma.ray-v2:0 模型已在 us-west-2 啟用" -ForegroundColor Gray
Write-Host "  2. S3 Buckets 需要先在 AWS Console 建立（如果不存在）" -ForegroundColor Gray
