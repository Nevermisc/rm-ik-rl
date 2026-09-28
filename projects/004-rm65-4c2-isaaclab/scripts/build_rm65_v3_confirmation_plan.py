#!/usr/bin/env python3
"""Preregister a fresh 20-case confirmation plan before RM65 v3 training."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLAN_FORMAT = "rm65_pi05_sim_evaluation_plan_deterministic_v1"
ANGLES = (0.6625, 0.7375, 0.8125, 0.9125)
OFFSETS = (
    (-0.009, -0.002),
    (-0.004, 0.009),
    (0.002, -0.008),
    (0.009, 0.004),
    (0.0, 0.006),
)
PROMPTS = (
    "pick up the block and place it on the target",
    "move the block onto the target",
    "grasp the block and set it on the target",
    "place the block on the target platform",
    "pick the block and put it at the target",
)


def condition(case: dict[str, Any]) -> tuple[float, float, float]:
    return (
        case["transfer_joint_1_rad"],
        case["source_offset_x_m"],
        case["source_offset_y_m"],
    )


def build_plan(policy_seed_start: int, simulation_seed_start: int) -> dict[str, Any]:
    cases = []
    for angle_index, angle in enumerate(ANGLES):
        for offset_index, (offset_x, offset_y) in enumerate(OFFSETS):
            index = len(cases)
            cases.append(
                {
                    "case_id": f"confirm_v3_{index:03d}",
                    "panel": "fresh_continuous_interpolation",
                    "policy_noise_seed": policy_seed_start + index,
                    "simulation_seed": simulation_seed_start + index,
                    "transfer_joint_1_rad": angle,
                    "source_offset_x_m": offset_x,
                    "source_offset_y_m": offset_y,
                    "prompt": PROMPTS[(angle_index + offset_index) % len(PROMPTS)],
                }
            )
    return {
        "format": PLAN_FORMAT,
        "description": (
            "Preregistered fresh-condition confirmation for the RM65 pi0.5 "
            "failure-correction v3 checkpoint. Created before v3 training."
        ),
        "evaluation_kind": "fresh_held_out_interpolation_after_failure_correction",
        "preregistration": {
            "created_at": "2026-09-28",
            "created_before_v3_training": True,
            "normal_model_failures_must_not_be_retried": True,
            "infrastructure_retries_require_missing_valid_report": True,
            "conditions_must_not_be_added_to_training_before_confirmation": True,
        },
        "gate": {
            "minimum_episode_count": 20,
            "minimum_success_rate": 0.9,
            "require_all_planned_reports": True,
        },
        "sampling_contract": {
            "mode": "explicit_numpy_gaussian_noise_v1",
            "chunk_seed_rule": "policy_noise_seed + chunk_index",
            "prior_plan_seed_overlap": False,
        },
        "cases": cases,
    }


def validate_plan(
    plan: dict[str, Any],
    training_plans: list[dict[str, Any]],
    excluded_plans: list[dict[str, Any]],
) -> dict[str, Any]:
    cases = plan["cases"]
    conditions = [condition(case) for case in cases]
    training_cases = [
        case for prior in training_plans for case in prior.get("cases", [])
    ]
    training_conditions = {condition(case) for case in training_cases}
    training_angles = {
        case["transfer_joint_1_rad"] for case in training_cases
    }
    prior_cases = [
        case for prior in excluded_plans for case in prior.get("cases", [])
    ]
    prior_conditions = {condition(case) for case in prior_cases}
    prior_policy_seeds = {
        case["policy_noise_seed"]
        for case in prior_cases
        if isinstance(case.get("policy_noise_seed"), int)
    }
    prior_simulation_seeds = {
        case["simulation_seed"]
        for case in prior_cases
        if isinstance(case.get("simulation_seed"), int)
    }
    prompt_counts = Counter(case["prompt"] for case in cases)
    angle_counts = Counter(case["transfer_joint_1_rad"] for case in cases)
    checks = {
        "format_supported": plan.get("format") == PLAN_FORMAT,
        "twenty_cases": len(cases) == 20,
        "unique_case_ids": len({case["case_id"] for case in cases}) == 20,
        "unique_conditions": len(set(conditions)) == 20,
        "four_balanced_angles": sorted(angle_counts.values()) == [5, 5, 5, 5],
        "five_balanced_prompts": sorted(prompt_counts.values()) == [4, 4, 4, 4, 4],
        "conditions_held_out_from_training": set(conditions).isdisjoint(training_conditions),
        "angles_held_out_from_training": set(ANGLES).isdisjoint(training_angles),
        "conditions_held_out_from_prior_evaluation": set(conditions).isdisjoint(prior_conditions),
        "policy_seeds_held_out": {
            case["policy_noise_seed"] for case in cases
        }.isdisjoint(prior_policy_seeds),
        "simulation_seeds_held_out": {
            case["simulation_seed"] for case in cases
        }.isdisjoint(prior_simulation_seeds),
        "strict_ninety_percent_gate": plan.get("gate", {}).get("minimum_success_rate") == 0.9,
    }
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "status": "pass" if not failed else "fail",
        "checks": checks,
        "failed_checks": failed,
        "case_count": len(cases),
        "training_case_count_considered": len(training_cases),
        "prior_evaluation_case_count_considered": len(prior_cases),
        "angles_rad": list(ANGLES),
        "offsets_m": [list(offset) for offset in OFFSETS],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training-plan", type=Path, action="append", required=True)
    parser.add_argument("--exclude-plan", type=Path, action="append", default=[])
    parser.add_argument("--policy-seed-start", type=int, default=690928000)
    parser.add_argument("--simulation-seed-start", type=int, default=790928000)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "config" / "rm65_pi05_failure_correction_v3_confirmation_20.json",
    )
    parser.add_argument(
        "--validation-output",
        type=Path,
        default=PROJECT_ROOT / "results" / "rm65_pi05_failure_correction_v3_confirmation_20_validation.json",
    )
    args = parser.parse_args()
    if args.policy_seed_start < 0 or args.simulation_seed_start < 0:
        raise ValueError("seed starts must be non-negative")
    training_plans = [
        json.loads(path.read_text(encoding="utf-8")) for path in args.training_plan
    ]
    excluded_plans = [
        json.loads(path.read_text(encoding="utf-8")) for path in args.exclude_plan
    ]
    plan = build_plan(args.policy_seed_start, args.simulation_seed_start)
    validation = validate_plan(plan, training_plans, excluded_plans)
    if validation["status"] != "pass":
        print(json.dumps(validation, indent=2))
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    args.validation_output.parent.mkdir(parents=True, exist_ok=True)
    args.validation_output.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(validation, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

