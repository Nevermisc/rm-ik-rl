#!/usr/bin/env python3
"""Audit repeated RM65 pi0.5 runs across identical cases and seeds."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np


OBSERVATION_FIELDS = (
    "joint_position",
    "gripper_position",
    "external_image",
    "wrist_image",
)
PHYSICAL_STATE_FIELDS = (
    "cube_position",
    "cube_quaternion",
    "wrist_tool_position",
    "wrist_tool_quaternion",
    "wrist_camera_eye",
    "wrist_camera_forward",
)
METRIC_FIELDS = (
    "block_lift_height_m",
    "final_target_xy_error_m",
    "final_target_position_error_m",
    "post_release_drift_m",
    "final_gripper_normalized",
)


def load_valid_report(
    root: Path,
    case: dict[str, Any],
    checkpoint_id: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    path = root / case["case_id"] / "task_report.json"
    if not path.is_file():
        return None, ["missing_report"]
    report = json.loads(path.read_text(encoding="utf-8"))
    expected_offsets = [
        float(case.get("source_offset_x_m")),
        float(case.get("source_offset_y_m")),
    ]
    try:
        report_angle = float(report.get("transfer_joint_1_rad"))
        report_offsets = [float(value) for value in report.get("source_offset_xy_m", [])]
    except (TypeError, ValueError):
        report_angle = None
        report_offsets = []
    checks = {
        "status": report.get("status") in {"pass", "fail"},
        "simulation_only": report.get("simulation_only") is True,
        "real_robot_command_sent": report.get("real_robot_command_sent") is False,
        "pi05_used": report.get("pi05_used") is True,
        "checkpoint": report.get("policy_checkpoint_id") == checkpoint_id,
        "policy_noise_seed": report.get("policy_noise_seed") == case.get("policy_noise_seed"),
        "simulation_seed": report.get("simulation_seed") == case.get("simulation_seed"),
        "prompt": report.get("prompt") == case.get("prompt"),
        "transfer_joint_1_rad": report_angle is not None
        and abs(report_angle - float(case.get("transfer_joint_1_rad"))) <= 1e-9,
        "source_offset_xy_m": len(report_offsets) == 2
        and all(
            abs(actual - expected) <= 1e-9
            for actual, expected in zip(report_offsets, expected_offsets, strict=True)
        ),
        "action_chunks_positive": isinstance(report.get("action_chunks"), int)
        and report["action_chunks"] > 0,
        "executed_actions_positive": isinstance(report.get("executed_actions"), int)
        and report["executed_actions"] > 0,
    }
    failed = [name for name, passed in checks.items() if not passed]
    return (report if not failed else None), failed


def all_same(values: list[Any], expected_count: int) -> bool:
    return len(values) == expected_count and all(value is not None for value in values) and len(set(values)) == 1


def summarize_metric(values: list[Any]) -> dict[str, Any]:
    numeric = [float(value) for value in values if isinstance(value, (int, float))]
    if not numeric:
        return {"count": 0, "mean": None, "std": None, "minimum": None, "maximum": None, "range": None}
    array = np.asarray(numeric, dtype=np.float64)
    return {
        "count": len(numeric),
        "mean": float(array.mean()),
        "std": float(array.std()),
        "minimum": float(array.min()),
        "maximum": float(array.max()),
        "range": float(array.max() - array.min()),
    }


def build_analysis(
    plan: dict[str, Any],
    run_roots: list[Path],
) -> dict[str, Any]:
    cases = plan.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("repeatability plan has no cases")
    if len(run_roots) < 2:
        raise ValueError("at least two run roots are required")
    expected_repeat_count = plan.get("preregistration", {}).get("repeat_count")
    if expected_repeat_count is not None and len(run_roots) != expected_repeat_count:
        raise ValueError(
            f"plan requires {expected_repeat_count} repeats, got {len(run_roots)}"
        )
    checkpoint_id = plan.get("frozen_controller_contract", {}).get("checkpoint_id")
    if not isinstance(checkpoint_id, str):
        raise ValueError("repeatability plan is missing checkpoint_id")

    run_summaries = [
        {
            "run_index": index,
            "root": str(root.resolve()),
            "valid_report_count": 0,
            "success_count": 0,
        }
        for index, root in enumerate(run_roots)
    ]
    invalid_reports: list[dict[str, Any]] = []
    case_results: list[dict[str, Any]] = []
    for case in cases:
        reports: list[dict[str, Any]] = []
        report_slots: list[dict[str, Any] | None] = []
        for run_index, root in enumerate(run_roots):
            report, failures = load_valid_report(root, case, checkpoint_id)
            report_slots.append(report)
            if report is None:
                invalid_reports.append(
                    {
                        "case_id": case["case_id"],
                        "run_index": run_index,
                        "root": str(root.resolve()),
                        "failures": failures,
                    }
                )
                continue
            reports.append(report)
            run_summaries[run_index]["valid_report_count"] += 1
            run_summaries[run_index]["success_count"] += report.get("status") == "pass"

        statuses = [report.get("status") for report in reports]
        chunks = [
            report.get("deterministic_sampling", {}).get("chunks", [{}])[0]
            for report in reports
        ]
        observation_hashes = {
            field: [chunk.get("observation_sha256", {}).get(field) for chunk in chunks]
            for field in OBSERVATION_FIELDS
        }
        physical_state_hashes = {
            field: [chunk.get("observation_sha256", {}).get(field) for chunk in chunks]
            for field in PHYSICAL_STATE_FIELDS
        }
        case_results.append(
            {
                "case_id": case["case_id"],
                "panel": case.get("panel"),
                "policy_noise_seed": case.get("policy_noise_seed"),
                "simulation_seed": case.get("simulation_seed"),
                "report_count": len(reports),
                "statuses": statuses,
                "status_consistent": all_same(statuses, len(run_roots)),
                "outcome_flip": len(reports) == len(run_roots) and len(set(statuses)) > 1,
                "chunk_zero_hash_matches": {
                    **{
                        field: all_same(values, len(run_roots))
                        for field, values in observation_hashes.items()
                    },
                    "noise": all_same(
                        [chunk.get("noise_sha256") for chunk in chunks], len(run_roots)
                    ),
                    "raw_action": all_same(
                        [chunk.get("raw_action_sha256") for chunk in chunks], len(run_roots)
                    ),
                },
                "chunk_zero_physical_state_hashes": {
                    field: {
                        "available": len(values) == len(run_roots)
                        and all(value is not None for value in values),
                        "match": (
                            all_same(values, len(run_roots))
                            if len(values) == len(run_roots)
                            and all(value is not None for value in values)
                            else None
                        ),
                    }
                    for field, values in physical_state_hashes.items()
                },
                "exact_initial_policy_observation_present": all(
                    isinstance(report.get("initial_policy_observation"), dict)
                    for report in reports
                )
                and len(reports) == len(run_roots),
                "metrics": {
                    field: summarize_metric([report.get(field) for report in reports])
                    for field in METRIC_FIELDS
                },
            }
        )

    for summary in run_summaries:
        summary["failure_count"] = summary["valid_report_count"] - summary["success_count"]
        summary["success_rate"] = (
            summary["success_count"] / summary["valid_report_count"]
            if summary["valid_report_count"]
            else 0.0
        )

    complete_cases = [result for result in case_results if result["report_count"] == len(run_roots)]
    status_consistent_count = sum(result["status_consistent"] for result in complete_cases)
    outcome_flip_count = sum(result["outcome_flip"] for result in complete_cases)
    status_consistency_rate = status_consistent_count / len(cases)
    hash_match_counts = {
        key: sum(result["chunk_zero_hash_matches"][key] for result in complete_cases)
        for key in (*OBSERVATION_FIELDS, "noise", "raw_action")
    }
    physical_state_hash_available_case_counts = {
        field: sum(
            result["chunk_zero_physical_state_hashes"][field]["available"]
            for result in complete_cases
        )
        for field in PHYSICAL_STATE_FIELDS
    }
    physical_state_hash_match_case_counts = {
        field: sum(
            result["chunk_zero_physical_state_hashes"][field]["match"] is True
            for result in complete_cases
        )
        for field in PHYSICAL_STATE_FIELDS
    }
    gate_config = plan.get("repeatability_gate", {})
    expected_reports = len(cases) * len(run_roots)
    checks = {
        "all_reports_valid": len(invalid_reports) == 0 and len(complete_cases) == len(cases),
        "required_report_count_met": sum(summary["valid_report_count"] for summary in run_summaries)
        == gate_config.get("required_reports", expected_reports),
        "minimum_status_consistency_rate_met": status_consistency_rate
        >= float(gate_config.get("minimum_status_consistency_rate", 1.0)),
        "maximum_outcome_flip_cases_met": outcome_flip_count
        <= int(gate_config.get("maximum_outcome_flip_cases", 0)),
        "initial_joint_hash_match": hash_match_counts["joint_position"] == len(cases),
        "initial_gripper_hash_match": hash_match_counts["gripper_position"] == len(cases),
        "chunk_zero_noise_hash_match": hash_match_counts["noise"] == len(cases),
        "all_simulation_only": True,
        "no_real_robot_commands": True,
    }
    passed = all(checks.values())
    outcome_patterns = Counter("/".join(result["statuses"]) for result in complete_cases)
    return {
        "status": "pass" if passed else "fail",
        "analysis_kind": "rm65_pi05_repeatability_matrix_v1",
        "simulation_only": True,
        "real_robot_command_sent": False,
        "run_count": len(run_roots),
        "planned_case_count": len(cases),
        "expected_report_count": expected_reports,
        "valid_report_count": sum(summary["valid_report_count"] for summary in run_summaries),
        "status_consistent_case_count": status_consistent_count,
        "status_consistency_rate": status_consistency_rate,
        "outcome_flip_case_count": outcome_flip_count,
        "chunk_zero_hash_match_case_counts": hash_match_counts,
        "chunk_zero_physical_state_hash_available_case_counts": (
            physical_state_hash_available_case_counts
        ),
        "chunk_zero_physical_state_hash_match_case_counts": (
            physical_state_hash_match_case_counts
        ),
        "exact_initial_policy_observation_case_count": sum(
            result["exact_initial_policy_observation_present"] for result in complete_cases
        ),
        "outcome_patterns": dict(sorted(outcome_patterns.items())),
        "run_summaries": run_summaries,
        "gate": {"passed": passed, "checks": checks, "config": gate_config},
        "invalid_reports": invalid_reports,
        "cases": case_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    analysis = build_analysis(plan, args.run_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in analysis.items() if key != "cases"}, indent=2))
    return 0 if analysis["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
