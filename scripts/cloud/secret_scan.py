"""Fail CI/deployment when likely credentials are embedded in project files."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

AWS_ACCESS_KEY = re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")
AWS_SECRET_ASSIGNMENT = re.compile(
    r"(?i)(?:aws_secret_access_key|secret_access_key)\s*[:=]\s*[\"']?([^\s\"']+)"
)
MYSQL_URL = re.compile(r"mysql(?:\+mysqlconnector)?://([^:\s/]+):([^@\s]+)@[^\s\"']+")
PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")

PLACEHOLDERS = {
    "change_me",
    "changeme",
    "your_password",
    "your-password",
    "password",
    "example",
    "***",
    "<password>",
    "${database_password}",
}
SKIP_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
}
SKIP_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".zip", ".pdf", ".mp3",
    ".wav", ".aiff", ".pyc", ".so", ".dylib", ".lock",
}


def _is_placeholder(value: str) -> bool:
    normalized = value.strip().strip('"\'').lower()
    return (
        normalized in PLACEHOLDERS
        or "change_me" in normalized
        or "example" in normalized
        or normalized.startswith("your_")
        or normalized.endswith("_here")
        or normalized in {"encoded_password", "rds_password"}
    )


def _candidate_files(root: Path) -> list[Path]:
    if (root / ".git").exists() and shutil.which("git"):
        try:
            output = subprocess.check_output(
                ["git", "-C", str(root), "ls-files", "-z"],
                stderr=subprocess.DEVNULL,
            )
            return [root / item.decode("utf-8") for item in output.split(b"\0") if item]
        except (OSError, subprocess.CalledProcessError, UnicodeDecodeError):
            pass
    return [path for path in root.rglob("*") if path.is_file()]


def scan(root: Path) -> list[str]:
    findings: list[str] = []
    for path in _candidate_files(root):
        if not path.is_file():
            continue
        if SKIP_PARTS.intersection(path.parts) or path.suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(root)
        for line_no, line in enumerate(text.splitlines(), start=1):
            if AWS_ACCESS_KEY.search(line):
                findings.append(f"{rel}:{line_no}: possible AWS access key")
            secret_match = AWS_SECRET_ASSIGNMENT.search(line)
            if secret_match and not _is_placeholder(secret_match.group(1)):
                findings.append(f"{rel}:{line_no}: possible AWS secret assignment")
            for mysql_match in MYSQL_URL.finditer(line):
                if not _is_placeholder(mysql_match.group(2)):
                    findings.append(f"{rel}:{line_no}: MySQL URL contains a non-placeholder password")
            if PRIVATE_KEY.search(line):
                findings.append(f"{rel}:{line_no}: private key material")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    findings = scan(root)
    if findings:
        print("Secret scan failed:", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    print(f"Secret scan passed: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
