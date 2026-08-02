#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-us-west-2}"
SERVICE_NAME="${SERVICE_NAME:-smart-care-agent}"
STACK_NAME="${STACK_NAME:-smart-care-agent-ecs}"
ECR_REPOSITORY="${ECR_REPOSITORY:-smart-care-agent}"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)}"
DATABASE_SECRET_NAME="${DATABASE_SECRET_NAME:-smart-care-agent/database-url}"
API_TOKEN_SECRET_NAME="${API_TOKEN_SECRET_NAME:-smart-care-agent/api-bearer-token}"
BEDROCK_MODEL_ID="${BEDROCK_MODEL_ID:-us.anthropic.claude-haiku-4-5-20251001-v1:0}"
WHISPER_MODEL_SIZE="${WHISPER_MODEL_SIZE:-small}"
ASR_MODE="${ASR_MODE:-hybrid}"
BREEZE_ASR_ENABLED="${BREEZE_ASR_ENABLED:-false}"
TAIWANESE_TTS_ENABLED="${TAIWANESE_TTS_ENABLED:-false}"
INSTALL_BILINGUAL_VOICE="${INSTALL_BILINGUAL_VOICE:-false}"
PRELOAD_BREEZE="${PRELOAD_BREEZE:-false}"
PRELOAD_TAIWANESE_TTS="${PRELOAD_TAIWANESE_TTS:-false}"
CREATE_PRIVATE_ENDPOINTS="${CREATE_PRIVATE_ENDPOINTS:-true}"

required=(VPC_ID PRIVATE_SUBNET_IDS PRIVATE_ROUTE_TABLE_IDS RDS_SECURITY_GROUP_ID DEMO_USER_ID DEMO_PERSONA_ID DATABASE_URL API_BEARER_TOKEN)
for name in "${required[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: $name" >&2
    exit 2
  fi
done

python3 scripts/cloud/secret_scan.py .
aws sts get-caller-identity --region "$REGION" >/dev/null
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPOSITORY}"

aws ecr describe-repositories --region "$REGION" --repository-names "$ECR_REPOSITORY" >/dev/null 2>&1 \
  || aws ecr create-repository \
       --region "$REGION" \
       --repository-name "$ECR_REPOSITORY" \
       --image-scanning-configuration scanOnPush=true >/dev/null

aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

if [[ "$BREEZE_ASR_ENABLED" == "true" || "$TAIWANESE_TTS_ENABLED" == "true" ]]; then
  if [[ "$INSTALL_BILINGUAL_VOICE" != "true" ]]; then
    echo "BREEZE_ASR_ENABLED/TAIWANESE_TTS_ENABLED requires INSTALL_BILINGUAL_VOICE=true" >&2
    exit 2
  fi
fi

docker build \
  --platform linux/arm64 \
  --build-arg "PRELOAD_WHISPER_MODEL=${WHISPER_MODEL_SIZE}" \
  --build-arg "INSTALL_BILINGUAL_VOICE=${INSTALL_BILINGUAL_VOICE}" \
  --build-arg "PRELOAD_BREEZE=${PRELOAD_BREEZE}" \
  --build-arg "PRELOAD_TAIWANESE_TTS=${PRELOAD_TAIWANESE_TTS}" \
  --tag "${ECR_URI}:${IMAGE_TAG}" .
docker push "${ECR_URI}:${IMAGE_TAG}"

DATABASE_SECRET_ARN="$(scripts/cloud/create_or_update_secret.sh "$DATABASE_SECRET_NAME" DATABASE_URL)"
API_TOKEN_SECRET_ARN="$(scripts/cloud/create_or_update_secret.sh "$API_TOKEN_SECRET_NAME" API_BEARER_TOKEN)"

aws cloudformation deploy \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --template-file infra/ecs/stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    "ServiceName=${SERVICE_NAME}" \
    "EcrImageUri=${ECR_URI}:${IMAGE_TAG}" \
    "VpcId=${VPC_ID}" \
    "PrivateSubnetIds=${PRIVATE_SUBNET_IDS}" \
    "PrivateRouteTableIds=${PRIVATE_ROUTE_TABLE_IDS}" \
    "RdsSecurityGroupId=${RDS_SECURITY_GROUP_ID}" \
    "DatabaseUrlSecretArn=${DATABASE_SECRET_ARN}" \
    "ApiBearerTokenSecretArn=${API_TOKEN_SECRET_ARN}" \
    "BedrockModelId=${BEDROCK_MODEL_ID}" \
    "DemoUserId=${DEMO_USER_ID}" \
    "DemoPersonaId=${DEMO_PERSONA_ID}" \
    "WhisperModelSize=${WHISPER_MODEL_SIZE}" \
    "AsrMode=${ASR_MODE}" \
    "BreezeAsrEnabled=${BREEZE_ASR_ENABLED}" \
    "TaiwaneseTtsEnabled=${TAIWANESE_TTS_ENABLED}" \
    "CreatePrivateEndpoints=${CREATE_PRIVATE_ENDPOINTS}"

SERVICE_URL="$(aws cloudformation describe-stacks \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='ServiceUrl'].OutputValue" \
  --output text)"

echo "Deployment completed."
echo "Service URL: ${SERVICE_URL}"
echo "Validation UI: ${SERVICE_URL}/demo"
echo "Smoke test: BASE_URL=${SERVICE_URL} API_BEARER_TOKEN='***' python3 scripts/cloud/smoke_cloud.py --full-agent"
