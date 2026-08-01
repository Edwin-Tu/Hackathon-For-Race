#!/usr/bin/env bash
set -euo pipefail

SG_ID="${1:-${RDS_SECURITY_GROUP_ID:-}}"
REGION="${AWS_REGION:-us-west-2}"

if [[ -z "$SG_ID" ]]; then
  echo "Usage: $0 <rds-security-group-id>" >&2
  exit 2
fi

PUBLIC_RULES="$(aws ec2 describe-security-groups \
  --region "$REGION" \
  --group-ids "$SG_ID" \
  --query "SecurityGroups[0].IpPermissions[?FromPort==\`3306\` && ToPort==\`3306\`].IpRanges[?CidrIp=='0.0.0.0/0'].CidrIp" \
  --output text)"

if [[ -z "$PUBLIC_RULES" ]]; then
  echo "No public 0.0.0.0/0 MySQL rule found on $SG_ID."
  exit 0
fi

aws ec2 revoke-security-group-ingress \
  --region "$REGION" \
  --group-id "$SG_ID" \
  --protocol tcp \
  --port 3306 \
  --cidr 0.0.0.0/0

echo "Revoked public MySQL ingress from $SG_ID."
