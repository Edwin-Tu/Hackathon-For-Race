"""Non-destructive cloud deployment preflight."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from scripts.cloud.secret_scan import scan


def _csv(name: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


def main() -> int:
    failures: list[str] = []
    root = Path(__file__).resolve().parents[2]
    findings = scan(root)
    if findings:
        failures.extend(findings)

    for command in ("aws", "docker"):
        if shutil.which(command) is None:
            failures.append(f"required command not found: {command}")

    region = os.getenv("AWS_REGION", "us-west-2")
    try:
        identity = boto3.client("sts", region_name=region).get_caller_identity()
        print(f"AWS account: {identity.get('Account')} ({identity.get('Arn')})")
    except (BotoCoreError, ClientError) as exc:
        failures.append(f"AWS credentials/STS failed: {type(exc).__name__}")

    required = (
        "VPC_ID",
        "PRIVATE_SUBNET_IDS",
        "PRIVATE_ROUTE_TABLE_IDS",
        "RDS_SECURITY_GROUP_ID",
        "DEMO_USER_ID",
        "DEMO_PERSONA_ID",
        "DATABASE_URL",
        "API_BEARER_TOKEN",
    )
    for name in required:
        if not os.getenv(name):
            failures.append(f"missing environment variable: {name}")

    subnets = _csv("PRIVATE_SUBNET_IDS")
    route_tables = _csv("PRIVATE_ROUTE_TABLE_IDS")
    if subnets and len(subnets) < 2:
        failures.append("PRIVATE_SUBNET_IDS must contain at least two subnets")
    if route_tables and not all(item.startswith("rtb-") for item in route_tables):
        failures.append("PRIVATE_ROUTE_TABLE_IDS contains an invalid route table ID")
    if subnets and not all(item.startswith("subnet-") for item in subnets):
        failures.append("PRIVATE_SUBNET_IDS contains an invalid subnet ID")

    database_url = os.getenv("DATABASE_URL", "")
    if database_url:
        parsed = urlparse(database_url)
        if parsed.scheme not in {"mysql", "mysql+mysqlconnector"}:
            failures.append("DATABASE_URL must use mysql://")
        if parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
            failures.append("cloud DATABASE_URL must not point to localhost")
        if not parsed.hostname or not parsed.username or not parsed.path.strip("/"):
            failures.append("DATABASE_URL must include user, host, and database")

    token = os.getenv("API_BEARER_TOKEN", "")
    if token and len(token) < 32:
        failures.append("API_BEARER_TOKEN must be at least 32 characters")

    if failures:
        print("Preflight failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Cloud preflight passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
