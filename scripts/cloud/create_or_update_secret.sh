#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <secret-name> <environment-variable-name>" >&2
  exit 2
fi

SECRET_NAME="$1"
VALUE_ENV="$2"
VALUE="${!VALUE_ENV:-}"
REGION="${AWS_REGION:-us-west-2}"

if [[ -z "$VALUE" ]]; then
  echo "$VALUE_ENV is empty; refusing to create a blank secret." >&2
  exit 2
fi

TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT
chmod 600 "$TMP_FILE"
printf '%s' "$VALUE" > "$TMP_FILE"

if aws secretsmanager describe-secret --region "$REGION" --secret-id "$SECRET_NAME" >/dev/null 2>&1; then
  aws secretsmanager put-secret-value \
    --region "$REGION" \
    --secret-id "$SECRET_NAME" \
    --secret-string "file://$TMP_FILE" >/dev/null
else
  aws secretsmanager create-secret \
    --region "$REGION" \
    --name "$SECRET_NAME" \
    --secret-string "file://$TMP_FILE" >/dev/null
fi

aws secretsmanager describe-secret \
  --region "$REGION" \
  --secret-id "$SECRET_NAME" \
  --query ARN \
  --output text
