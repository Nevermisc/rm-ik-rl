#!/usr/bin/env python3
"""Build compact evidence after replacing false preflight reports with first policy executions."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from compact_closed_loop_suite_summary import compact_case


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def wilson_interval(successes: int, total: int) -> list[float]:
    if total == 0:
        return [0.0, 0.0]
    z = 1.959963984540054
    proportion = successes / total
    denominator = 1.0 + z * z / total
    center = (proportion + z * z / (2.0 * total)) / denominator
    margin = (
        z
        * math.sqrt(
            proportion * (1.0 - proportion) / total + z * z / (4.0 * total * total)
        )
        / denominator
    )
    return [center - margin, center + margin]


def summarize_group(rows: list[tuple[dict[str, Any], dict[str, Any]]], key: str) -> dict:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case, report in rows:
        grouped[str(case.get(key))].append(report)
    return {
        group: {
            "total": len(reports),
            "passes": sum(report.get("status") == "pass" for report in reports),
            "success_rate": sum(report.get("status") == "pass" for report in reports)
            / len(reports),
        }
        for group, reports in sorted(grouped.items())
    }


def validate_replacement(
    case: dict[str, Any],
    report: dict[str, Any],
    checkpoint_id: str,
) -> None:
    case_id = case["case_id"]
    checks = {
        "simulation_only": report.get("simulation_only") is True,
        "real_robot_command_sent": report.get("real_robot_command_sent") is False,
        "pi05_used": report.get("pi05_used") is True,
        "checkpoint": report.get("policy_checkpoint_id") == checkpoint_id,
        "policy_noise_seed": report.get("policy_noise_seed") == case.get("policy_noise_seed"),
        "simulation_seed": report.get("simulation_seed") == case.get("simulation_seed"),
        "action_chunks_positive": isinstance(report.get("action_chunks"), int)
        and report["action_chunks"] > 0,
        "executed_actions_positive": isinstance(report.get("executed_actions"), int)
        and report["executed_actions"] > 0,
        "no_preflight_failure": report.get("preflight_failure") is None,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError(f"replacement report {case_id} failed checks: {failed}")


def build_evidence(
    plan: dict[str, Any],
    base_summary: dict[str, Any],
    base_summary_path: Path,
    replacement_root: Path,
    replacement_case_ids: list[str],
) -> dict[str, Any]:
    plan_cases = plan.get("cases")
    summary_cases = base_summary.get("cases")
    if not isinstance(plan_cases, list) or not plan_cases:
        raise ValueError("evaluation plan has no cases")
    if not isinstance(summary_cases, list) or len(summary_cases) != len(plan_cases):
        raise ValueError("base summary does not contain every planned case")

    plan_by_id = {case["case_id"]: case for case in plan_cases}
    corrected_cases = copy.deepcopy(summary_cases)
    summary_by_id = {case["case_id"]: case for case in corrected_cases}
    if set(plan_by_id) != set(summary_by_id):
        raise ValueError("base summary case ids do not match the plan")

    replacements = []
    checkpoint_id = base_summary.get("policy_checkpoint_id")
    for case_id in replacement_case_ids:
        if case_id not in plan_by_id:
            raise ValueError(f"replacement case is not in the plan: {case_id}")
        report_path = replacement_root / case_id / "task_report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        validate_replacement(plan_by_id[case_id], report, checkpoint_id)
        destination = summary_by_id[case_id]
        previous_report = destination.get("report") or {}
        replacements.append(
            {
                "case_id": case_id,
                "previous_status": previous_report.get("status"),
                "previous_preflight_failure": previous_report.get("preflight_failure"),
                "first_policy_execution_status": report.get("status"),
                "action_chunks": report.get("action_chunks"),
                "executed_actions": report.get("executed_actions"),
                "report_path": str(report_path.resolve()),
                "report_sha256": sha256_file(report_path),
            }
        )
        destination["report"] = report
        destination["runner_returncode"] = 0
        destination["timed_out"] = False
        destination["reused"] = False
        destination["correction_replacement"] = True

    rows = [(case, summary_by_id[case["case_id"]]["report"]) for case in plan_cases]
    valid_reports = [report for _, report in rows if report.get("status") in {"pass", "fail"}]
    successes = sum(report.get("status") == "pass" for report in valid_reports)
    planned = len(plan_cases)
    complete = len(valid_reports) == planned
    success_rate = successes / len(valid_reports) if valid_reports else 0.0
    gate = {
        "passed": len(valid_reports) >= 20 and complete and success_rate >= 0.8,
        "minimum_episode_count": 20,
        "minimum_success_rate": 0.8,
        "require_all_planned_reports": True,
        "missing_report_count": planned - len(valid_reports),
    }
    gate["checks"] = {
        "minimum_episode_count_met": len(valid_reports) >= 20,
        "all_planned_reports_present": complete,
        "minimum_success_rate_met": success_rate >= 0.8,
    }

    return {
        "status": "pass" if gate["passed"] else "fail",
        "evidence_kind": "rm65_pi05_corrected_first_policy_execution_v1",
        "simulation_only": True,
        "real_robot_command_sent": False,
        "plan": base_summary.get("plan"),
        "checkpoint": base_summary.get("checkpoint"),
        "policy_checkpoint_id": checkpoint_id,
        "repo_id": base_summary.get("repo_id"),
        "correction": {
            "reason": (
                "The replaced reports were false preflight rejections caused by an unused "
                "scripted-only place trajectory in pi0.5 mode."
            ),
            "base_summary": str(base_summary_path.resolve()),
            "base_summary_sha256": sha256_file(base_summary_path),
            "replacement_root": str(replacement_root.resolve()),
            "replacement_case_ids": replacement_case_ids,
            "replacement_policy": "first actual pi0.5 execution for each affected case",
        },
        "planned_case_count": planned,
        "episode_count": len(valid_reports),
        "success_count": successes,
        "failure_count": len(valid_reports) - successes,
        "success_rate": success_rate,
        "success_rate_ci95_wilson": wilson_interval(successes, len(valid_reports)),
        "gate": gate,
        "by_panel": summarize_group(rows, "panel"),
        "by_transfer_joint_1_rad": summarize_group(rows, "transfer_joint_1_rad"),
        "by_prompt": summarize_group(rows, "prompt"),
        "replacements": replacements,
        "cases": [compact_case(summary_by_id[case["case_id"]]) for case in plan_cases],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--base-summary", type=Path, required=True)
    parser.add_argument("--replacement-root", type=Path, required=True)
    parser.add_argument("--replacement-case-id", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    base_summary = json.loads(args.base_summary.read_text(encoding="utf-8"))
    evidence = build_evidence(
        plan,
        base_summary,
        args.base_summary,
        args.replacement_root,
        args.replacement_case_id,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in evidence.items() if key != "cases"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
