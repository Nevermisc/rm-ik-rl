#!/usr/bin/env python3
"""Compare two RM65 pi0.5 IsaacLab closed-loop evaluation summaries."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.expanduser().resolve().read_text(encoding="utf-8"))


def validate_summary(summary: dict, label: str) -> None:
    if summary.get("evaluation_kind") != "isaaclab_pi0.5_closed_loop":
        raise ValueError(f"{label} is not an RM65 pi0.5 closed-loop summary")
    if summary.get("simulation_only") is not True:
        raise ValueError(f"{label} is not marked simulation_only")
    if summary.get("real_robot_command_sent") is not False:
        raise ValueError(f"{label} does not prove real_robot_command_sent=false")


def report_statuses(summary: dict) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for item in summary.get("cases", []):
        case_id = item["case_id"]
        if case_id in statuses:
            raise ValueError(f"duplicate case id in summary: {case_id}")
        report = item.get("report")
        status = report.get("status") if isinstance(report, dict) else "missing"
        statuses[case_id] = status if status in {"pass", "fail"} else "missing"
    return statuses


def transition(before: str, after: str) -> str:
    if before == "fail" and after == "pass":
        return "improved"
    if before == "pass" and after == "fail":
        return "regressed"
    if before == "pass" and after == "pass":
        return "stable_pass"
    if before == "fail" and after == "fail":
        return "stable_fail"
    if before == "missing":
        return "missing_in_baseline"
    return "missing_in_candidate"


def rate_record(rows: list[dict]) -> dict:
    baseline_valid = [row for row in rows if row["baseline_status"] in {"pass", "fail"}]
    candidate_valid = [row for row in rows if row["candidate_status"] in {"pass", "fail"}]
    baseline_successes = sum(row["baseline_status"] == "pass" for row in baseline_valid)
    candidate_successes = sum(row["candidate_status"] == "pass" for row in candidate_valid)
    baseline_rate = baseline_successes / len(baseline_valid) if baseline_valid else None
    candidate_rate = candidate_successes / len(candidate_valid) if candidate_valid else None
    return {
        "case_count": len(rows),
        "baseline_valid_count": len(baseline_valid),
        "baseline_success_count": baseline_successes,
        "baseline_success_rate": baseline_rate,
        "candidate_valid_count": len(candidate_valid),
        "candidate_success_count": candidate_successes,
        "candidate_success_rate": candidate_rate,
        "success_rate_delta": (
            candidate_rate - baseline_rate
            if baseline_rate is not None and candidate_rate is not None
            else None
        ),
    }


def compare(baseline: dict, candidate: dict, plan: dict) -> dict:
    validate_summary(baseline, "baseline")
    validate_summary(candidate, "candidate")
    baseline_statuses = report_statuses(baseline)
    candidate_statuses = report_statuses(candidate)

    rows = []
    for case in plan.get("cases", []):
        case_id = case["case_id"]
        before = baseline_statuses.get(case_id, "missing")
        after = candidate_statuses.get(case_id, "missing")
        rows.append(
            {
                "case_id": case_id,
                "prompt": case["prompt"],
                "transfer_joint_1_rad": case["transfer_joint_1_rad"],
                "source_offset_x_m": case["source_offset_x_m"],
                "source_offset_y_m": case["source_offset_y_m"],
                "baseline_status": before,
                "candidate_status": after,
                "transition": transition(before, after),
            }
        )
    if not rows:
        raise ValueError("evaluation plan has no cases")

    by_prompt: dict[str, list[dict]] = defaultdict(list)
    by_angle: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_prompt[row["prompt"]].append(row)
        by_angle[f'{row["transfer_joint_1_rad"]:.6f}'].append(row)

    overall = rate_record(rows)
    transitions = {
        name: sum(row["transition"] == name for row in rows)
        for name in (
            "improved",
            "regressed",
            "stable_pass",
            "stable_fail",
            "missing_in_baseline",
            "missing_in_candidate",
        )
    }
    candidate_gate = candidate.get("gate", {})
    minimum_count = int(candidate_gate.get("minimum_episode_count", 20))
    minimum_rate = float(candidate_gate.get("minimum_success_rate", 0.8))
    candidate_valid = int(candidate.get("episode_count", 0))
    candidate_rate = float(candidate.get("success_rate", 0.0))
    candidate_gate_pass = candidate_valid >= minimum_count and candidate_rate >= minimum_rate

    return {
        "status": "pass",
        "analysis_kind": "rm65_pi05_closed_loop_comparison",
        "simulation_only": True,
        "real_robot_command_sent": False,
        "baseline": {
            "checkpoint": baseline.get("checkpoint"),
            "repo_id": baseline.get("repo_id"),
            "episode_count": baseline.get("episode_count"),
            "success_count": baseline.get("success_count"),
            "success_rate": baseline.get("success_rate"),
        },
        "candidate": {
            "checkpoint": candidate.get("checkpoint"),
            "repo_id": candidate.get("repo_id"),
            "episode_count": candidate.get("episode_count"),
            "success_count": candidate.get("success_count"),
            "success_rate": candidate.get("success_rate"),
        },
        "overall_from_case_reports": overall,
        "transitions": transitions,
        "candidate_gate": {
            "minimum_episode_count": minimum_count,
            "minimum_success_rate": minimum_rate,
            "passed": candidate_gate_pass,
        },
        "by_prompt": {key: rate_record(value) for key, value in sorted(by_prompt.items())},
        "by_transfer_joint_1_rad": {
            key: rate_record(value) for key, value in sorted(by_angle.items())
        },
        "cases": rows,
        "interpretation": (
            "This report compares pi0.5 execution in IsaacLab only. "
            "Its pass status means the comparison was computed; candidate_gate.passed "
            "is the closed-loop acceptance result."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = compare(load_json(args.baseline), load_json(args.candidate), load_json(args.plan))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "cases"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
