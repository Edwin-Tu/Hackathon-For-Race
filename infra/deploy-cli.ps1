# deploy-cli.ps1 - AWS CLI deployment script
# Usage: .\deploy-cli.ps1

$ErrorActionPreference = "Continue"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI Video Generator - AWS Deployment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Settings
$Region = "us-west-2"
$ProjectName = "my-app"
$ImagesBucket = "$ProjectName-images-prod-$Region"
$VideosBucket = "$ProjectName-videos-prod-$Region"
$TableName = "VideoTasks"
$LambdaName = "$ProjectName-generate-video"
$LambdaRoleName = "$ProjectName-lambda-role"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Refresh PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
# AWS credentials should be configured via:
#   - AWS CLI: aws configure
#   - Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
#   - IAM role (for EC2/Lambda)
$env:AWS_DEFAULT_REGION = $Region

# Check AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Please install AWS CLI first" -ForegroundColor Red
    exit 1
}

# Check AWS credentials
Write-Host "`nStep 1: Checking AWS credentials..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
    Write-Host "OK AWS auth success (Account: $($identity.Account))" -ForegroundColor Green
}
catch {
    Write-Host "Error: AWS auth failed" -ForegroundColor Red
    exit 1
}

$AccountId = $identity.Account

# Step 2: Check DynamoDB Table
Write-Host "`nStep 2: Checking DynamoDB Table..." -ForegroundColor Yellow

$tableCheck = aws dynamodb describe-table --table-name $TableName --region $Region 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK DynamoDB Table '$TableName' exists" -ForegroundColor Green
}
else {
    Write-Host "WARNING DynamoDB Table '$TableName' not found" -ForegroundColor Yellow
    Write-Host "Please create Table in AWS Console with:" -ForegroundColor White
    Write-Host "  - Table Name: $TableName" -ForegroundColor Gray
    Write-Host "  - Partition Key: taskId (String)" -ForegroundColor Gray
    Write-Host "  - GSI: residentId-createdAt-index (residentId: HASH, createdAt: RANGE)" -ForegroundColor Gray
}

# Step 3: Check S3 Buckets
Write-Host "`nStep 3: Checking S3 Buckets..." -ForegroundColor Yellow

# Check Images Bucket
$imgCheck = aws s3api head-bucket --bucket $ImagesBucket --region $Region 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK Images Bucket '$ImagesBucket' exists" -ForegroundColor Green
    
    # Set CORS
    $corsFile = Join-Path $ScriptDir "policies/cors.json"
    aws s3api put-bucket-cors --bucket $ImagesBucket --cors-configuration "file://$corsFile" --region $Region
    Write-Host "OK CORS configured" -ForegroundColor Green
}
else {
    Write-Host "WARNING Images Bucket '$ImagesBucket' not found" -ForegroundColor Yellow
}

# Check Videos Bucket
$vidCheck = aws s3api head-bucket --bucket $VideosBucket --region $Region 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK Videos Bucket '$VideosBucket' exists" -ForegroundColor Green
}
else {
    Write-Host "WARNING Videos Bucket '$VideosBucket' not found" -ForegroundColor Yellow
}

# Step 4: Create Lambda IAM Role
Write-Host "`nStep 4: Checking/Creating Lambda IAM Role..." -ForegroundColor Yellow

$roleCheck = aws iam get-role --role-name $LambdaRoleName 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK IAM Role '$LambdaRoleName' exists" -ForegroundColor Green
}
else {
    Write-Host "Creating IAM Role..." -ForegroundColor White
    
    $trustFile = Join-Path $ScriptDir "policies/trust-policy.json"
    aws iam create-role --role-name $LambdaRoleName --assume-role-policy-document "file://$trustFile"

    # Attach basic execution policy
    aws iam attach-role-policy --role-name $LambdaRoleName --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

    # Create custom policy
    $customFile = Join-Path $ScriptDir "policies/lambda-policy.json"
    
    # Generate policy JSON
    $policyJson = '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["s3:GetObject","s3:PutObject"],"Resource":["arn:aws:s3:::' + $ImagesBucket + '/*","arn:aws:s3:::' + $VideosBucket + '/*"]},{"Effect":"Allow","Action":["dynamodb:GetItem","dynamodb:PutItem","dynamodb:UpdateItem","dynamodb:Query"],"Resource":["arn:aws:dynamodb:' + $Region + ':' + $AccountId + ':table/' + $TableName + '","arn:aws:dynamodb:' + $Region + ':' + $AccountId + ':table/' + $TableName + '/index/*"]},{"Effect":"Allow","Action":["bedrock:InvokeModel","bedrock:StartAsyncInvoke","bedrock:GetAsyncInvoke"],"Resource":"*"}]}'
    [System.IO.File]::WriteAllText($customFile, $policyJson)
    
    $policyName = $LambdaName + "-policy"
    aws iam put-role-policy --role-name $LambdaRoleName --policy-name $policyName --policy-document "file://$customFile"

    Write-Host "Waiting for Role to be available..." -ForegroundColor White
    Start-Sleep -Seconds 10
    Write-Host "OK IAM Role created" -ForegroundColor Green
}

$LambdaRoleArn = "arn:aws:iam::" + $AccountId + ":role/" + $LambdaRoleName

# Step 5: Package and deploy Lambda
Write-Host "`nStep 5: Packaging and deploying Lambda..." -ForegroundColor Yellow

$LambdaDir = Join-Path $ScriptDir "../lambda/generate-video"
$ZipPath = Join-Path $env:TEMP "generate-video.zip"

# Install dependencies
Push-Location $LambdaDir
npm install --production
Pop-Location

# Create ZIP
if (Test-Path $ZipPath) { Remove-Item $ZipPath }
Compress-Archive -Path "$LambdaDir/*" -DestinationPath $ZipPath -Force
Write-Host "OK Lambda packaged" -ForegroundColor Green

# Check if Lambda exists
$lambdaCheck = aws lambda get-function --function-name $LambdaName --region $Region 2>&1
$lambdaExists = ($LASTEXITCODE -eq 0)

# Create environment variables JSON
$envJson = '{"Variables":{"AWS_S3_IMAGES_BUCKET":"' + $ImagesBucket + '","AWS_S3_VIDEOS_BUCKET":"' + $VideosBucket + '","AWS_DYNAMODB_TABLE_VIDEO_TASKS":"' + $TableName + '","AWS_BEDROCK_MODEL_ID":"luma.ray-v2:0"}}'
$envFile = Join-Path $env:TEMP "lambda-env.json"
[System.IO.File]::WriteAllText($envFile, $envJson)

if ($lambdaExists) {
    Write-Host "Updating Lambda function..." -ForegroundColor White
    aws lambda update-function-code --function-name $LambdaName --zip-file "fileb://$ZipPath" --region $Region | Out-Null
    
    Start-Sleep -Seconds 5
    aws lambda update-function-configuration --function-name $LambdaName --timeout 300 --memory-size 512 --environment "file://$envFile" --region $Region | Out-Null
    Write-Host "OK Lambda updated" -ForegroundColor Green
}
else {
    Write-Host "Creating Lambda function..." -ForegroundColor White
    aws lambda create-function --function-name $LambdaName --runtime nodejs20.x --role $LambdaRoleArn --handler index.handler --zip-file "fileb://$ZipPath" --timeout 300 --memory-size 512 --environment "file://$envFile" --region $Region | Out-Null
    Write-Host "OK Lambda created" -ForegroundColor Green
}

# Step 6: Configure S3 Event trigger
Write-Host "`nStep 6: Configuring S3 Event trigger..." -ForegroundColor Yellow

$LambdaArn = "arn:aws:lambda:" + $Region + ":" + $AccountId + ":function:" + $LambdaName

# Allow S3 to invoke Lambda
aws lambda add-permission --function-name $LambdaName --statement-id "s3-trigger" --action "lambda:InvokeFunction" --principal s3.amazonaws.com --source-arn "arn:aws:s3:::$ImagesBucket" --region $Region 2>&1 | Out-Null

# Configure S3 notification
$notificationJson = '{"LambdaFunctionConfigurations":[{"LambdaFunctionArn":"' + $LambdaArn + '","Events":["s3:ObjectCreated:*"],"Filter":{"Key":{"FilterRules":[{"Name":"prefix","Value":"images/"}]}}}]}'
$notificationFile = Join-Path $env:TEMP "s3-notification.json"
[System.IO.File]::WriteAllText($notificationFile, $notificationJson)

$s3NotifyResult = aws s3api put-bucket-notification-configuration --bucket $ImagesBucket --notification-configuration "file://$notificationFile" --region $Region 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK S3 Event trigger configured" -ForegroundColor Green
}
else {
    Write-Host "WARNING S3 Event config failed: $s3NotifyResult" -ForegroundColor Yellow
}

# Done
Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "  Deployment Complete!" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Created/Updated resources:" -ForegroundColor White
Write-Host "  - IAM Role: $LambdaRoleName" -ForegroundColor Gray
Write-Host "  - Lambda: $LambdaName" -ForegroundColor Gray
Write-Host ""
Write-Host "Please verify .env.local settings:" -ForegroundColor Yellow
Write-Host "  AWS_S3_IMAGES_BUCKET=$ImagesBucket"
Write-Host "  AWS_S3_VIDEOS_BUCKET=$VideosBucket"
Write-Host "  AWS_DYNAMODB_TABLE_VIDEO_TASKS=$TableName"
Write-Host ""
Write-Host "Notes:" -ForegroundColor Yellow
Write-Host "  1. Make sure Bedrock luma.ray-v2:0 model is enabled in us-west-2" -ForegroundColor Gray
Write-Host "  2. If S3 Buckets or DynamoDB Table don't exist, create them in AWS Console first" -ForegroundColor Gray
