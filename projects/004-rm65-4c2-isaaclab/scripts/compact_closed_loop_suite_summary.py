#!/usr/bin/env python3
"""Write compact, reviewable evidence from a full RM65 closed-loop suite summary."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


TOP_LEVEL_KEYS = (
    "status",
    "evaluation_kind",
    "simulation_only",
    "real_robot_command_sent",
    "plan",
    "checkpoint",
    "policy_checkpoint_id",
    "repo_id",
    "gripper_open_threshold_normalized",
    "gripper_actual_open_threshold_normalized",
    "policy_max_action_chunks",
    "diagnostic_only",
    "deterministic_sampling",
    "planned_case_count",
    "episode_count",
    "success_count",
    "success_rate",
    "gate",
)

METRIC_KEYS = (
    "source_to_target_xy_distance_m",
    "block_lift_height_m",
    "final_target_xy_error_m",
    "final_target_position_error_m",
    "post_release_drift_m",
    "final_gripper_normalized",
    "all_states_finite",
)


def chunk_evidence_sha256(report: dict) -> str:
    chunks = report.get("deterministic_sampling", {}).get("chunks", [])
    evidence = [
        {
            "chunk_index": chunk.get("chunk_index"),
            "seed": chunk.get("seed"),
            "noise_sha256": chunk.get("noise_sha256"),
            "observation_sha256": chunk.get("observation_sha256"),
            "raw_action_sha256": chunk.get("raw_action_sha256"),
            "safe_action_sha256": chunk.get("safe_action_sha256"),
        }
        for chunk in chunks
    ]
    canonical = json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def compact_case(case: dict) -> dict:
    report = case.get("report") or {}
    release = report.get("release_verification", {})
    episode = report.get("episode", {})
    return {
        "case_id": case.get("case_id"),
        "policy_noise_seed": case.get("policy_noise_seed"),
        "simulation_seed": case.get("simulation_seed"),
        "runner_returncode": case.get("runner_returncode"),
        "timed_out": case.get("timed_out", False),
        "reused": case.get("reused", False),
        "status": report.get("status"),
        "action_chunks": report.get("action_chunks"),
        "executed_actions": report.get("executed_actions"),
        "simulation_safety_abort_reason": report.get(
            "simulation_safety_abort_reason"
        ),
        "release_verified": release.get("verified"),
        "episode_validation_status": episode.get("validation", {}).get("status"),
        "deterministic_chunk_evidence_sha256": chunk_evidence_sha256(report),
        "metrics": {key: report.get(key) for key in METRIC_KEYS},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source = json.loads(args.input.read_text(encoding="utf-8"))
    compact = {key: source.get(key) for key in TOP_LEVEL_KEYS}
    compact["evidence_kind"] = "rm65_pi05_closed_loop_suite_compact_evidence_v1"
    compact["cases"] = [compact_case(case) for case in source.get("cases", [])]
    compact["all_reports_present"] = len(compact["cases"]) == source.get(
        "planned_case_count"
    ) and all(case["status"] in {"pass", "fail"} for case in compact["cases"])
    compact["all_cases_simulation_only"] = all(
        (case.get("report") or {}).get("simulation_only") is True
        and (case.get("report") or {}).get("real_robot_command_sent") is False
        for case in source.get("cases", [])
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(compact, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": compact["status"],
                "success_count": compact["success_count"],
                "episode_count": compact["episode_count"],
                "success_rate": compact["success_rate"],
                "all_reports_present": compact["all_reports_present"],
                "all_cases_simulation_only": compact["all_cases_simulation_only"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
