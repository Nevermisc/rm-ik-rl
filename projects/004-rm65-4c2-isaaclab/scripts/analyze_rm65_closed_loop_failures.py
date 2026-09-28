#!/usr/bin/env python3
"""Summarize RM65 pi0.5 closed-loop reports into a failure taxonomy."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path


SIMULATION_BOUNDS_M = {
    "maximum_absolute_xy": 2.0,
    "minimum_z": -1.0,
    "maximum_z": 2.0,
}


def simulation_out_of_bounds(report: dict) -> bool:
    position = report.get("final_position_m")
    if not isinstance(position, list) or len(position) != 3:
        return False
    if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in position):
        return False
    x, y, z = (float(value) for value in position)
    return bool(
        abs(x) > SIMULATION_BOUNDS_M["maximum_absolute_xy"]
        or abs(y) > SIMULATION_BOUNDS_M["maximum_absolute_xy"]
        or z < SIMULATION_BOUNDS_M["minimum_z"]
        or z > SIMULATION_BOUNDS_M["maximum_z"]
    )


def failed_criteria(report: dict) -> list[str]:
    preflight = report.get("preflight_failure")
    if isinstance(preflight, dict):
        reason = preflight.get("reason", "unknown")
        return [f"preflight_safety_rejection:{reason}"]
    failures: list[str] = []
    if not report.get("all_states_finite", False):
        failures.append("nonfinite_state")
    if simulation_out_of_bounds(report):
        failures.append("simulation_out_of_bounds")
    if report.get("source_to_target_xy_distance_m", 0.0) <= 0.12:
        failures.append("insufficient_displacement")
    if report.get("block_lift_height_m", 0.0) <= 0.02:
        failures.append("insufficient_lift")
    if report.get("final_target_xy_error_m", float("inf")) >= 0.05:
        failures.append("target_xy_error")
    if report.get("final_target_position_error_m", float("inf")) >= 0.05:
        failures.append("target_position_error")
    if report.get("post_release_drift_m", float("inf")) >= 0.02:
        failures.append("post_release_drift")
    release_verification = report.get("release_verification")
    if isinstance(release_verification, dict):
        if release_verification.get("verified") is not True:
            failures.append("release_not_verified")
    else:
        historical_threshold = report.get("criteria", {}).get(
            "final_gripper_normalized_lt", 0.12
        )
        if report.get("final_gripper_normalized", float("inf")) >= historical_threshold:
            failures.append("gripper_not_open")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--episode-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    cases = plan.get("cases", [])
    failure_counts: Counter[str] = Counter()
    prompt_totals: Counter[str] = Counter()
    prompt_passes: Counter[str] = Counter()
    angle_totals: Counter[str] = Counter()
    angle_passes: Counter[str] = Counter()
    details: list[dict] = []
    status_counts: Counter[str] = Counter()

    for case in cases:
        case_id = case["case_id"]
        prompt = case["prompt"]
        angle = f"{float(case['transfer_joint_1_rad']):.2f}"
        prompt_totals[prompt] += 1
        angle_totals[angle] += 1
        report_path = args.episode_root / case_id / "task_report.json"
        if not report_path.is_file():
            status_counts["missing_report"] += 1
            failure_counts["missing_report"] += 1
            details.append(
                {
                    "case_id": case_id,
                    "status": "missing_report",
                    "prompt": prompt,
                    "transfer_joint_1_rad": float(case["transfer_joint_1_rad"]),
                    "failures": ["missing_report"],
                }
            )
            continue

        report = json.loads(report_path.read_text(encoding="utf-8"))
        status = report.get("status", "unknown")
        status_counts[status] += 1
        failures = [] if status == "pass" else failed_criteria(report)
        failure_counts.update(failures)
        if status == "pass":
            prompt_passes[prompt] += 1
            angle_passes[angle] += 1
        details.append(
            {
                "case_id": case_id,
                "status": status,
                "prompt": prompt,
                "transfer_joint_1_rad": float(case["transfer_joint_1_rad"]),
                "source_offset_x_m": float(case["source_offset_x_m"]),
                "source_offset_y_m": float(case["source_offset_y_m"]),
                "failures": failures,
                "metrics": {
                    key: report.get(key)
                    for key in (
                        "source_to_target_xy_distance_m",
                        "block_lift_height_m",
                        "final_target_position_error_m",
                        "post_release_drift_m",
                        "final_gripper_normalized",
                        "release_verification",
                    )
                },
            }
        )

    pass_count = status_counts["pass"]
    valid_count = pass_count + status_counts["fail"]
    result = {
        "status": "pass" if valid_count == len(cases) else "fail",
        "analysis_kind": "rm65_pi05_closed_loop_failure_taxonomy",
        "simulation_only": True,
        "real_robot_command_sent": False,
        "simulation_bounds_m": SIMULATION_BOUNDS_M,
        "planned_case_count": len(cases),
        "valid_report_count": valid_count,
        "success_count": pass_count,
        "success_rate_over_valid_reports": pass_count / valid_count if valid_count else 0.0,
        "status_counts": dict(sorted(status_counts.items())),
        "failure_counts": dict(sorted(failure_counts.items())),
        "by_prompt": {
            prompt: {
                "total": total,
                "passes": prompt_passes[prompt],
                "success_rate": prompt_passes[prompt] / total,
            }
            for prompt, total in sorted(prompt_totals.items())
        },
        "by_transfer_joint_1_rad": {
            angle: {
                "total": total,
                "passes": angle_passes[angle],
                "success_rate": angle_passes[angle] / total,
            }
            for angle, total in sorted(angle_totals.items())
        },
        "cases": details,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "cases"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
