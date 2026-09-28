#!/usr/bin/env python3
"""Compare two same-case RM65 pi0.5 simulation task reports for reproducibility."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


METRIC_KEYS = (
    "source_to_target_xy_distance_m",
    "block_lift_height_m",
    "final_target_xy_error_m",
    "final_target_position_error_m",
    "post_release_drift_m",
    "final_gripper_normalized",
)
OBSERVATION_KEYS = (
    "joint_position",
    "gripper_position",
    "external_image",
    "wrist_image",
)


def load(path: Path) -> dict:
    return json.loads(path.expanduser().resolve().read_text(encoding="utf-8"))


def chunks(report: dict) -> list[dict]:
    value = report.get("deterministic_sampling", {}).get("chunks", [])
    return value if isinstance(value, list) else []


def first_divergence(first: list[Any], second: list[Any]) -> int | None:
    for index, (left, right) in enumerate(zip(first, second, strict=False)):
        if left != right:
            return index
    if len(first) != len(second):
        return min(len(first), len(second))
    return None


def compare(first: dict, second: dict) -> dict:
    first_chunks = chunks(first)
    second_chunks = chunks(second)
    first_noise = [item.get("noise_sha256") for item in first_chunks]
    second_noise = [item.get("noise_sha256") for item in second_chunks]
    first_raw = [item.get("raw_action_sha256") for item in first_chunks]
    second_raw = [item.get("raw_action_sha256") for item in second_chunks]
    first_safe = [item.get("safe_action_sha256") for item in first_chunks]
    second_safe = [item.get("safe_action_sha256") for item in second_chunks]
    observation_divergence = {}
    observation_complete = True
    for key in OBSERVATION_KEYS:
        left = [item.get("observation_sha256", {}).get(key) for item in first_chunks]
        right = [item.get("observation_sha256", {}).get(key) for item in second_chunks]
        if any(value is None for value in left + right):
            observation_complete = False
        observation_divergence[key] = first_divergence(left, right)

    metric_comparison = {}
    for key in METRIC_KEYS:
        left = first.get(key)
        right = second.get(key)
        metric_comparison[key] = {
            "first": left,
            "second": right,
            "exact_match": left == right,
            "absolute_delta": (
                abs(float(right) - float(left))
                if isinstance(left, (int, float)) and isinstance(right, (int, float))
                else None
            ),
        }

    checks = {
        "checkpoint_matches": first.get("policy_checkpoint_id")
        == second.get("policy_checkpoint_id"),
        "policy_noise_seed_matches": first.get("policy_noise_seed")
        == second.get("policy_noise_seed"),
        "simulation_seed_present_and_matches": isinstance(first.get("simulation_seed"), int)
        and first.get("simulation_seed") == second.get("simulation_seed"),
        "simulation_determinism_config_matches": first.get("simulation_determinism")
        == second.get("simulation_determinism"),
        "chunk_count_matches": len(first_chunks) == len(second_chunks),
        "noise_hashes_bit_exact": first_noise == second_noise and bool(first_noise),
        "observation_hashes_complete": observation_complete and bool(first_chunks),
        "observation_hashes_bit_exact": observation_complete
        and all(value is None for value in observation_divergence.values()),
        "raw_action_hashes_bit_exact": first_raw == second_raw and bool(first_raw),
        "safe_action_hashes_bit_exact": first_safe == second_safe and bool(first_safe),
        "task_status_matches": first.get("status") == second.get("status"),
        "task_metrics_bit_exact": all(
            item["exact_match"] for item in metric_comparison.values()
        ),
    }
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "status": "pass" if not failed else "fail",
        "validation_kind": "rm65_pi05_deterministic_simulation_comparison",
        "simulation_only": True,
        "real_robot_command_sent": False,
        "checks": checks,
        "failed_checks": failed,
        "first_divergence": {
            "noise_sha256_chunk": first_divergence(first_noise, second_noise),
            "observation_sha256_chunk_by_field": observation_divergence,
            "raw_action_sha256_chunk": first_divergence(first_raw, second_raw),
            "safe_action_sha256_chunk": first_divergence(first_safe, second_safe),
        },
        "first_run": {
            "status": first.get("status"),
            "action_chunks": len(first_chunks),
            "policy_noise_seed": first.get("policy_noise_seed"),
            "simulation_seed": first.get("simulation_seed"),
        },
        "second_run": {
            "status": second.get("status"),
            "action_chunks": len(second_chunks),
            "policy_noise_seed": second.get("policy_noise_seed"),
            "simulation_seed": second.get("simulation_seed"),
        },
        "metrics": metric_comparison,
        "interpretation": (
            "PASS requires bit-exact noise, observations, raw/safe actions, task status, and metrics. "
            "A failed comparison is diagnostic evidence and must not be reported as task success."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = compare(load(args.first), load(args.second))
    text = json.dumps(report, indent=2) + "\n"
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
