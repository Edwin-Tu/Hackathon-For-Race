#!/usr/bin/env python3
"""Evaluate InputGuardService against the bundled OWASP LLM01/02/07 dataset."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from secretguard.input_guard import InputGuardRequest, InputGuardService


def evaluate(dataset_path: Path) -> dict:
    with dataset_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    service = InputGuardService()
    failures: list[dict] = []
    split_stats: dict[str, Counter] = defaultdict(Counter)
    owasp_stats: dict[str, Counter] = defaultdict(Counter)

    for row in rows:
        decision = service.inspect(
            InputGuardRequest(
                request_id=row["id"],
                session_id=row["id"],
                text=row["prompt"],
                user_role="guest",
                authorization_status="unauthorized",
                metadata={"prior_context": row.get("prior_context", "")},
            )
        )
        acceptable = set(row["acceptable_actions"].split("|"))
        passed = decision.action.value in acceptable
        split_stats[row["dataset_split"]]["total"] += 1
        split_stats[row["dataset_split"]]["passed"] += int(passed)
        split_stats[row["dataset_split"]][f"action_{decision.action.value}"] += 1
        owasp_stats[row["owasp_id"]]["total"] += 1
        owasp_stats[row["owasp_id"]]["passed"] += int(passed)
        if not passed:
            failures.append(
                {
                    "id": row["id"],
                    "expected": sorted(acceptable),
                    "actual": decision.action.value,
                    "primary_category": decision.primary_category,
                    "risk_score": decision.overall_risk_score,
                }
            )

    total = len(rows)
    passed = total - len(failures)
    attack_rows = [r for r in rows if r["dataset_split"] == "attack"]
    normal_rows = [r for r in rows if r["dataset_split"] != "attack"]
    attack_failures = [f for f in failures if f["id"].startswith("LLM")]
    normal_failures = [f for f in failures if f["id"].startswith("NORMAL")]

    return {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": len(failures),
            "pass_rate": round(passed / total, 4) if total else 0.0,
            "attack_total": len(attack_rows),
            "attack_passed": len(attack_rows) - len(attack_failures),
            "normal_total": len(normal_rows),
            "normal_passed": len(normal_rows) - len(normal_failures),
        },
        "by_split": {name: dict(stats) for name, stats in split_stats.items()},
        "by_owasp_id": {name: dict(stats) for name, stats in owasp_stats.items()},
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("tests/data/input_guard_owasp_llm01_02_07_dataset.csv"),
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    report = evaluate(args.dataset)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
