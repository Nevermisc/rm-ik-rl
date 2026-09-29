#!/usr/bin/env python3
"""Recover one frozen RM65 failure report after an invalid infrastructure retry.

This utility is intentionally fail-closed and only accepts an original model
failure printed immediately before ``RM65_PI05_CLOSED_LOOP=...``.  It adds the
physical condition fields that were missing from the historical pi0.5 report
schema while preserving the original outcome and recording content hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REPORT_MARKER = "\nRM65_PI05_CLOSED_LOOP="
REPORT_START = '\n{\n  "status"'


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_report(log_text: str) -> tuple[dict[str, Any], str]:
    log_text = log_text.replace("\r\n", "\n")
    marker_index = log_text.rfind(REPORT_MARKER)
    if marker_index < 0:
        raise ValueError("runner log has no RM65 closed-loop result marker")
    report_start = log_text.rfind(REPORT_START, 0, marker_index)
    if report_start < 0:
        raise ValueError("runner log has no pretty-printed task report before marker")
    raw_report = log_text[report_start + 1 : marker_index].strip()
    report = json.loads(raw_report)
    if not isinstance(report, dict):
        raise ValueError("extracted report is not a JSON object")
    return report, raw_report


def recover_report(
    runner_log: Path,
    plan: dict[str, Any],
    case_id: str,
    excluded_retry_root: Path,
) -> dict[str, Any]:
    cases = {
        case.get("case_id"): case
        for case in plan.get("cases", [])
        if isinstance(case, dict)
    }
    if case_id not in cases:
        raise ValueError(f"case is not present in frozen plan: {case_id}")
    case = cases[case_id]
    log_bytes = runner_log.read_bytes()
    report, raw_report = extract_report(log_bytes.decode("utf-8"))
    controller = plan.get("frozen_controller_contract", {})
    expected = {
        "status": "fail",
        "simulation_only": True,
        "real_robot_command_sent": False,
        "pi05_used": True,
        "policy_checkpoint_id": controller.get("checkpoint_id"),
        "policy_noise_seed": case.get("policy_noise_seed"),
        "simulation_seed": case.get("simulation_seed"),
        "prompt": case.get("prompt"),
    }
    mismatches = {
        key: {"expected": value, "actual": report.get(key)}
        for key, value in expected.items()
        if report.get(key) != value
    }
    if mismatches:
        raise ValueError(f"original failure report contract mismatch: {mismatches}")
    if report.get("transfer_joint_1_rad") is not None:
        raise ValueError("original report already has transfer_joint_1_rad")
    if report.get("source_offset_xy_m") is not None:
        raise ValueError("original report already has source_offset_xy_m")

    recovered = dict(report)
    recovered["transfer_joint_1_rad"] = float(case["transfer_joint_1_rad"])
    recovered["source_offset_xy_m"] = [
        float(case["source_offset_x_m"]),
        float(case["source_offset_y_m"]),
    ]
    recovered["formal_outcome_recovery"] = {
        "format": "rm65_runner_log_failure_recovery_v1",
        "reason": "valid model failure was misclassified as a missing report because physical condition fields were absent",
        "source_runner_log": str(runner_log.resolve()),
        "source_runner_log_sha256": sha256(log_bytes),
        "extracted_original_report_sha256": sha256(raw_report.encode("utf-8")),
        "fields_added_from_frozen_plan": [
            "transfer_joint_1_rad",
            "source_offset_xy_m",
        ],
        "outcome_changed": False,
        "normal_model_failure_preserved": True,
        "invalid_retry_result_excluded": True,
        "excluded_retry_artifact_root": str(excluded_retry_root.resolve()),
        "original_episode_artifacts_available": False,
        "limitation": (
            "The invalid retry overwrote the original episode files. The exact original "
            "task report remains recoverable from the immutable runner log and is kept as "
            "the formal failure outcome; the retry PASS is excluded."
        ),
    }
    return recovered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-log", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--excluded-retry-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    recovered = recover_report(
        args.runner_log,
        plan,
        args.case_id,
        args.excluded_retry_root,
    )
    args.output.parent.mkdir(parents=True, exist_ok=False)
    args.output.write_text(json.dumps(recovered, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "pass",
                "case_id": args.case_id,
                "formal_outcome": recovered["status"],
                "output": str(args.output.resolve()),
                "real_robot_command_sent": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
