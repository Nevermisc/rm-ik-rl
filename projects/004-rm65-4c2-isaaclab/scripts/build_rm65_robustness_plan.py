#!/usr/bin/env python3
"""Build and validate a preregistered 60-case RM65 pi0.5 robustness plan."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLAN_FORMAT = "rm65_pi05_sim_evaluation_plan_deterministic_v1"
ANGLES = (0.65, 0.75, 0.85, 0.95)
PROMPTS = (
    "pick up the block and place it on the target",
    "move the block onto the target",
    "grasp the block and set it on the target",
    "place the block on the target platform",
    "pick the block and put it at the target",
)
PANEL_OFFSETS = {
    "panel_a_inner": (
        (-0.00375, -0.00375),
        (-0.00375, 0.00375),
        (0.00375, -0.00375),
        (0.00375, 0.00375),
        (0.0, 0.0),
    ),
    "panel_b_mid": (
        (-0.0075, 0.0),
        (0.0075, 0.0),
        (0.0, -0.0075),
        (0.0, 0.0075),
        (0.0075, 0.0075),
    ),
    "panel_c_outer": (
        (-0.01125, -0.01125),
        (-0.01125, 0.01125),
        (0.01125, -0.01125),
        (0.01125, 0.01125),
        (0.0, -0.01125),
    ),
}


def build_plan(policy_seed_start: int, simulation_seed_start: int) -> dict:
    cases = []
    for panel_index, (panel_id, offsets) in enumerate(PANEL_OFFSETS.items()):
        for angle_index, angle in enumerate(ANGLES):
            for offset_index, (offset_x, offset_y) in enumerate(offsets):
                case_index = len(cases)
                prompt_index = (offset_index + angle_index + 2 * panel_index) % len(
                    PROMPTS
                )
                cases.append(
                    {
                        "case_id": f"robust_{case_index:03d}",
                        "panel": panel_id,
                        "policy_noise_seed": policy_seed_start + case_index,
                        "simulation_seed": simulation_seed_start + case_index,
                        "transfer_joint_1_rad": angle,
                        "source_offset_x_m": offset_x,
                        "source_offset_y_m": offset_y,
                        "prompt": PROMPTS[prompt_index],
                    }
                )

    return {
        "format": PLAN_FORMAT,
        "description": (
            "Preregistered 60-case fresh-seed robustness evaluation for the frozen "
            "RM65 pi0.5 v2 checkpoint and release supervisor."
        ),
        "preregistration": {
            "created_at": "2026-09-28",
            "inspect_aggregate_only_after_all_cases": True,
            "normal_model_failures_must_not_be_retried": True,
            "infrastructure_retries_require_missing_valid_report": True,
        },
        "sampling_contract": {
            "mode": "explicit_numpy_gaussian_noise_v1",
            "chunk_seed_rule": "policy_noise_seed + chunk_index",
            "simulation_seed_fields": (
                "Python, NumPy, Torch, CUDA, Warp, Replicator, PhysX enhanced "
                "determinism"
            ),
            "prior_plan_seed_overlap": False,
        },
        "frozen_controller_contract": {
            "checkpoint_id": "rm65_policy_window_v2_lora_30k/29999",
            "repo_id": "local/rm65_sim_policy_train",
            "policy_max_action_chunks": 120,
            "policy_gripper_open_threshold": 0.12,
            "actual_gripper_open_threshold": 0.20,
            "required_release_candidate_chunks": 2,
        },
        "panels": [
            {
                "panel": panel_id,
                "case_count": len(ANGLES) * len(offsets),
                "offsets_m": [list(offset) for offset in offsets],
            }
            for panel_id, offsets in PANEL_OFFSETS.items()
        ],
        "cases": cases,
    }


def load_seed_sets(paths: list[Path]) -> tuple[set[int], set[int]]:
    policy_seeds: set[int] = set()
    simulation_seeds: set[int] = set()
    for path in paths:
        plan = json.loads(path.read_text(encoding="utf-8"))
        for case in plan.get("cases", []):
            if isinstance(case.get("policy_noise_seed"), int):
                policy_seeds.add(case["policy_noise_seed"])
            if isinstance(case.get("simulation_seed"), int):
                simulation_seeds.add(case["simulation_seed"])
    return policy_seeds, simulation_seeds


def validate_plan(plan: dict, collection: dict, excluded_plans: list[dict]) -> dict:
    cases = plan["cases"]
    case_ids = [case["case_id"] for case in cases]
    policy_seeds = [case["policy_noise_seed"] for case in cases]
    simulation_seeds = [case["simulation_seed"] for case in cases]
    conditions = [
        (
            case["transfer_joint_1_rad"],
            case["source_offset_x_m"],
            case["source_offset_y_m"],
        )
        for case in cases
    ]

    demonstration_cases = collection["cases"]
    demonstration_angles = {
        case["transfer_joint_1_rad"] for case in demonstration_cases
    }
    demonstration_conditions = {
        (
            case["transfer_joint_1_rad"],
            case["source_offset_x_m"],
            case["source_offset_y_m"],
        )
        for case in demonstration_cases
    }
    demonstration_x = [case["source_offset_x_m"] for case in demonstration_cases]
    demonstration_y = [case["source_offset_y_m"] for case in demonstration_cases]

    prior_policy_seeds: set[int] = set()
    prior_simulation_seeds: set[int] = set()
    for prior_plan in excluded_plans:
        for case in prior_plan.get("cases", []):
            if isinstance(case.get("policy_noise_seed"), int):
                prior_policy_seeds.add(case["policy_noise_seed"])
            if isinstance(case.get("simulation_seed"), int):
                prior_simulation_seeds.add(case["simulation_seed"])

    panel_counts = Counter(case["panel"] for case in cases)
    angle_counts = Counter(case["transfer_joint_1_rad"] for case in cases)
    prompt_counts = Counter(case["prompt"] for case in cases)
    checks = {
        "format_supported": plan.get("format") == PLAN_FORMAT,
        "sixty_cases": len(cases) == 60,
        "unique_case_ids": len(set(case_ids)) == len(cases),
        "unique_policy_seeds": len(set(policy_seeds)) == len(cases),
        "unique_simulation_seeds": len(set(simulation_seeds)) == len(cases),
        "unique_kinematic_conditions": len(set(conditions)) == len(cases),
        "three_balanced_panels": sorted(panel_counts.values()) == [20, 20, 20],
        "four_balanced_angles": sorted(angle_counts.values()) == [15, 15, 15, 15],
        "five_balanced_prompts": sorted(prompt_counts.values()) == [12] * 5,
        "angles_held_out": set(ANGLES).isdisjoint(demonstration_angles),
        "angles_inside_demonstration_range": all(
            min(demonstration_angles) < angle < max(demonstration_angles)
            for angle in ANGLES
        ),
        "offsets_inside_demonstration_range": all(
            min(demonstration_x) <= case["source_offset_x_m"] <= max(demonstration_x)
            and min(demonstration_y)
            <= case["source_offset_y_m"]
            <= max(demonstration_y)
            for case in cases
        ),
        "full_conditions_held_out": set(conditions).isdisjoint(
            demonstration_conditions
        ),
        "policy_seeds_disjoint_from_prior_plans": set(policy_seeds).isdisjoint(
            prior_policy_seeds
        ),
        "simulation_seeds_disjoint_from_prior_plans": set(
            simulation_seeds
        ).isdisjoint(prior_simulation_seeds),
    }
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "status": "pass" if not failed else "fail",
        "checks": checks,
        "failed_checks": failed,
        "case_count": len(cases),
        "panel_counts": dict(sorted(panel_counts.items())),
        "angle_counts": {str(key): value for key, value in sorted(angle_counts.items())},
        "prompt_counts": dict(sorted(prompt_counts.items())),
        "policy_seed_range": [min(policy_seeds), max(policy_seeds)],
        "simulation_seed_range": [min(simulation_seeds), max(simulation_seeds)],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--collection-plan",
        type=Path,
        default=PROJECT_ROOT / "config" / "rm65_expert_collection_plan_v1.json",
    )
    parser.add_argument("--exclude-plan", type=Path, action="append", default=[])
    parser.add_argument("--policy-seed-start", type=int, default=490928000)
    parser.add_argument("--simulation-seed-start", type=int, default=590928000)
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "config"
            / "rm65_pi05_evaluation_plan_robustness_v3_60.json"
        ),
    )
    parser.add_argument(
        "--validation-output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "results"
            / "rm65_pi05_evaluation_plan_robustness_v3_60_validation.json"
        ),
    )
    args = parser.parse_args()

    if args.policy_seed_start < 0 or args.simulation_seed_start < 0:
        raise ValueError("seed starts must be non-negative")
    collection = json.loads(args.collection_plan.read_text(encoding="utf-8"))
    excluded_plans = [
        json.loads(path.read_text(encoding="utf-8")) for path in args.exclude_plan
    ]
    plan = build_plan(args.policy_seed_start, args.simulation_seed_start)
    validation = validate_plan(plan, collection, excluded_plans)
    if validation["status"] != "pass":
        print(json.dumps(validation, indent=2))
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    args.validation_output.parent.mkdir(parents=True, exist_ok=True)
    args.validation_output.write_text(
        json.dumps(validation, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(validation, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
