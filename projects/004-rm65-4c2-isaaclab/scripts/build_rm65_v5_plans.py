#!/usr/bin/env python3
"""Build evidence-driven RM65 v5 correction and fresh confirmation plans."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from build_rm65_v4_plans import PLAN_FORMAT, PROMPTS, condition


CORRECTION_ANGLE_DELTAS_RAD = (-0.0125, 0.0, 0.0125)
RENDER_REPEATS_PER_PHYSICAL_CONDITION = 4
CORRECTION_SIMULATION_SEED_START = 892029000
CONFIRMATION_ANGLES_RAD = (0.70625, 0.79375, 0.86875, 0.9875)
CONFIRMATION_OFFSETS_M = (
    (-0.010, 0.005),
    (-0.003, -0.010),
    (0.005, 0.010),
    (0.010, -0.005),
    (-0.001, 0.004),
)
EXPECTED_SOURCE_PATTERNS = Counter(
    {"fail/fail/fail": 3, "pass/pass/fail": 1}
)
CORRECTION_FOCUS_BY_CASE = {
    "confirm_v4_010": "grasp_lift_stability",
    "confirm_v4_011": "transport_workspace_retention",
    "confirm_v4_015": "target_edge_release_convergence",
    "confirm_v4_017": "cross_render_action_consistency",
}


def selected_development_cases(
    source_plan: dict[str, Any], repeatability: dict[str, Any]
) -> list[tuple[dict[str, Any], list[str]]]:
    if repeatability.get("status") != "pass":
        raise ValueError("v4 repeatability report gate is not pass")
    if repeatability.get("valid_report_count") != 60:
        raise ValueError("v4 repeatability report does not contain 60 valid reports")
    source_by_id = {case["case_id"]: case for case in source_plan.get("cases", [])}
    selected: list[tuple[dict[str, Any], list[str]]] = []
    for result in repeatability.get("cases", []):
        statuses = result.get("statuses")
        if not isinstance(statuses, list) or len(statuses) != 3:
            raise ValueError(f"invalid repeatability statuses: {result.get('case_id')}")
        if statuses == ["pass", "pass", "pass"]:
            continue
        case_id = result.get("case_id")
        if case_id not in source_by_id:
            raise ValueError(f"repeatability case is absent from source plan: {case_id}")
        selected.append((source_by_id[case_id], statuses))
    patterns = Counter("/".join(statuses) for _, statuses in selected)
    selected_ids = {source["case_id"] for source, _ in selected}
    if patterns != EXPECTED_SOURCE_PATTERNS:
        raise ValueError(f"unexpected v4 non-stable-success patterns: {dict(patterns)}")
    if selected_ids != set(CORRECTION_FOCUS_BY_CASE):
        raise ValueError(f"unexpected v4 correction case ids: {sorted(selected_ids)}")
    return selected


def build_correction_plan(
    source_plan: dict[str, Any], repeatability: dict[str, Any]
) -> dict[str, Any]:
    selected = selected_development_cases(source_plan, repeatability)
    cases: list[dict[str, Any]] = []
    for source, statuses in selected:
        for angle_delta in CORRECTION_ANGLE_DELTAS_RAD:
            variant = (
                "angle_exact"
                if angle_delta == 0
                else f"angle_{'minus' if angle_delta < 0 else 'plus'}_0p0125"
            )
            physical_group_id = f"{source['case_id']}_{variant}"
            physical_group_index = len(cases) // RENDER_REPEATS_PER_PHYSICAL_CONDITION
            simulation_seed = CORRECTION_SIMULATION_SEED_START + physical_group_index
            for render_repeat_index in range(RENDER_REPEATS_PER_PHYSICAL_CONDITION):
                index = len(cases)
                cases.append(
                    {
                        "case_id": f"correction_v5_{physical_group_id}_render_{render_repeat_index + 1}",
                        "episode_index": index,
                        "split": "train",
                        "transfer_joint_1_rad": round(
                            float(source["transfer_joint_1_rad"]) + angle_delta, 6
                        ),
                        "source_offset_x_m": float(source["source_offset_x_m"]),
                        "source_offset_y_m": float(source["source_offset_y_m"]),
                        "prompt": source["prompt"],
                        "source_evaluation_case_id": source["case_id"],
                        "source_outcome_pattern": "/".join(statuses),
                        "correction_focus": CORRECTION_FOCUS_BY_CASE[source["case_id"]],
                        "physical_group_id": physical_group_id,
                        "physical_variant": variant,
                        "render_repeat_index": render_repeat_index,
                        "render_repeat_count": RENDER_REPEATS_PER_PHYSICAL_CONDITION,
                        "simulation_seed": simulation_seed,
                    }
                )
    return {
        "format": "rm65_expert_collection_plan_v1",
        "plan_kind": "rm65_pi05_failure_correction_v5",
        "expert": "scripted",
        "simulation_only": True,
        "pi05_used": False,
        "real_robot_command_sent": False,
        "training_only": True,
        "evidence_source": "rm65_pi05_failure_correction_v4_repeatability_20x3",
        "selection_rule": "all v4 cases not PASS/PASS/PASS",
        "source_failure_or_flip_case_ids": [source["case_id"] for source, _ in selected],
        "source_v4_first_run_gate_passed": False,
        "source_v4_repeatability_gate_passed": True,
        "source_v4_plan_is_development_only": True,
        "source_v4_development_case_ids": [
            case["case_id"] for case in source_plan.get("cases", [])
        ],
        "angle_deltas_rad": list(CORRECTION_ANGLE_DELTAS_RAD),
        "render_repeats_per_physical_condition": RENDER_REPEATS_PER_PHYSICAL_CONDITION,
        "simulation_seed_contract": (
            "all render repeats in one physical group share one explicit seed"
        ),
        "case_count": len(cases),
        "train_case_count": len(cases),
        "validation_case_count": 0,
        "independent_confirmation_reuse_allowed": False,
        "cases": cases,
    }


def validate_correction_plan(plan: dict[str, Any]) -> dict[str, Any]:
    cases = plan.get("cases", [])
    groups: dict[str, list[dict[str, Any]]] = {}
    for case in cases:
        groups.setdefault(case.get("physical_group_id"), []).append(case)
    selected_ids = plan.get("source_failure_or_flip_case_ids", [])
    development_ids = plan.get("source_v4_development_case_ids", [])
    patterns = Counter(case.get("source_outcome_pattern") for case in cases)
    checks = {
        "format": plan.get("format") == "rm65_expert_collection_plan_v1",
        "plan_kind": plan.get("plan_kind") == "rm65_pi05_failure_correction_v5",
        "simulation_only": plan.get("simulation_only") is True,
        "no_real_robot_commands": plan.get("real_robot_command_sent") is False,
        "training_only": plan.get("training_only") is True,
        "four_evidence_selected_cases": set(selected_ids)
        == set(CORRECTION_FOCUS_BY_CASE),
        "all_twenty_v4_cases_development_only": len(development_ids) == 20,
        "v4_success_gate_failed": plan.get("source_v4_first_run_gate_passed") is False,
        "v4_repeatability_gate_passed": plan.get("source_v4_repeatability_gate_passed") is True,
        "confirmation_reuse_blocked": plan.get("independent_confirmation_reuse_allowed") is False,
        "forty_eight_cases": len(cases) == 48,
        "unique_case_ids": len({case.get("case_id") for case in cases}) == len(cases),
        "contiguous_episode_indices": [case.get("episode_index") for case in cases]
        == list(range(len(cases))),
        "all_train_split": all(case.get("split") == "train" for case in cases),
        "twelve_physical_groups": len(groups) == 12,
        "four_render_repeats_per_group": all(
            len(group) == RENDER_REPEATS_PER_PHYSICAL_CONDITION
            for group in groups.values()
        ),
        "group_physics_identical": all(
            len({condition(case) for case in group}) == 1 for group in groups.values()
        ),
        "group_render_indices_complete": all(
            sorted(case.get("render_repeat_index") for case in group)
            == list(range(RENDER_REPEATS_PER_PHYSICAL_CONDITION))
            for group in groups.values()
        ),
        "group_simulation_seed_identical": all(
            len({case.get("simulation_seed") for case in group}) == 1
            for group in groups.values()
        ),
        "physical_group_seeds_unique": len(
            {group[0].get("simulation_seed") for group in groups.values()}
        )
        == len(groups),
        "four_failure_focuses_present": {
            case.get("correction_focus") for case in cases
        }
        == set(CORRECTION_FOCUS_BY_CASE.values()),
        "source_patterns_preserved": patterns
        == Counter({"fail/fail/fail": 36, "pass/pass/fail": 12}),
        "angles_within_expert_range": all(
            0.60 <= case["transfer_joint_1_rad"] <= 1.00 for case in cases
        ),
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "validation_kind": "rm65_pi05_failure_correction_v5_plan",
        "checks": checks,
        "case_count": len(cases),
        "physical_group_count": len(groups),
        "selected_source_case_ids": selected_ids,
        "correction_focuses": sorted(
            {case.get("correction_focus") for case in cases}
        ),
    }


def build_confirmation_plan(
    policy_seed_start: int, simulation_seed_start: int
) -> dict[str, Any]:
    cases = []
    for angle_index, angle in enumerate(CONFIRMATION_ANGLES_RAD):
        for offset_index, (offset_x, offset_y) in enumerate(CONFIRMATION_OFFSETS_M):
            index = len(cases)
            cases.append(
                {
                    "case_id": f"confirm_v5_{index:03d}",
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
            "Preregistered fresh-condition confirmation for the RM65 pi0.5 v5 "
            "failure-correction checkpoint, frozen before v5 training."
        ),
        "evaluation_kind": "fresh_held_out_interpolation_after_v5_correction",
        "preregistration": {
            "created_at": "2026-09-29",
            "created_before_v5_training": True,
            "repeat_count": 3,
            "first_run_is_independent_success_confirmation": True,
            "later_runs_are_repeatability_evidence_not_new_success_trials": True,
            "normal_model_failures_must_not_be_retried": True,
            "infrastructure_retries_require_missing_valid_report": True,
            "conditions_must_not_be_added_to_training_before_confirmation": True,
            "v3_confirmation_plan_is_development_only": True,
            "v4_confirmation_plan_is_development_only": True,
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
        "frozen_controller_contract": {
            "checkpoint_id": "rm65_failure_correction_v5_lora_4k/3999",
            "repo_id": "local/rm65_sim_failure_correction_v5_train",
            "policy_max_action_chunks": 120,
            "policy_gripper_open_threshold": 0.12,
            "actual_gripper_open_threshold": 0.20,
            "required_release_candidate_chunks": 2,
            "cube_workspace_escape_radius_m": 1.0,
            "post_control_workspace_safety_checks_required": True,
        },
        "repeatability_gate": {
            "required_reports": 60,
            "minimum_status_consistency_rate": 0.95,
            "maximum_outcome_flip_cases": 1,
            "require_initial_joint_hash_match": True,
            "require_initial_gripper_hash_match": True,
            "require_chunk_zero_noise_hash_match": True,
            "image_and_action_hash_matches": "reported_but_not_required_until_renderer_fix",
        },
        "cases": cases,
    }


def validate_confirmation_plan(
    plan: dict[str, Any],
    training_plans: list[dict[str, Any]],
    excluded_evaluation_plans: list[dict[str, Any]],
) -> dict[str, Any]:
    cases = plan.get("cases", [])
    conditions = [condition(case) for case in cases]
    training_cases = [case for item in training_plans for case in item.get("cases", [])]
    prior_cases = [
        case for item in excluded_evaluation_plans for case in item.get("cases", [])
    ]
    training_conditions = {condition(case) for case in training_cases}
    prior_conditions = {condition(case) for case in prior_cases}
    training_angles = {condition(case)[0] for case in training_cases}
    prior_offsets = {
        (float(case["source_offset_x_m"]), float(case["source_offset_y_m"]))
        for case in training_cases + prior_cases
    }
    prior_policy_seeds = {
        case.get("policy_noise_seed") for case in prior_cases if "policy_noise_seed" in case
    }
    prior_simulation_seeds = {
        case.get("simulation_seed") for case in prior_cases if "simulation_seed" in case
    }
    prompts = Counter(case.get("prompt") for case in cases)
    angles = Counter(case.get("transfer_joint_1_rad") for case in cases)
    new_offsets = {
        (float(case["source_offset_x_m"]), float(case["source_offset_y_m"]))
        for case in cases
    }
    checks = {
        "format": plan.get("format") == PLAN_FORMAT,
        "twenty_cases": len(cases) == 20,
        "unique_case_ids": len({case.get("case_id") for case in cases}) == 20,
        "unique_conditions": len(set(conditions)) == 20,
        "four_balanced_angles": sorted(angles.values()) == [5, 5, 5, 5],
        "five_balanced_prompts": sorted(prompts.values()) == [4, 4, 4, 4, 4],
        "conditions_held_out_from_all_training": set(conditions).isdisjoint(training_conditions),
        "angles_held_out_from_all_training": set(CONFIRMATION_ANGLES_RAD).isdisjoint(training_angles),
        "offsets_held_out_from_training_and_prior_evaluation": new_offsets.isdisjoint(prior_offsets),
        "conditions_held_out_from_prior_evaluation": set(conditions).isdisjoint(prior_conditions),
        "policy_seeds_held_out": {case["policy_noise_seed"] for case in cases}.isdisjoint(prior_policy_seeds),
        "simulation_seeds_held_out": {case["simulation_seed"] for case in cases}.isdisjoint(prior_simulation_seeds),
        "created_before_training": plan.get("preregistration", {}).get("created_before_v5_training") is True,
        "v3_plan_development_only": plan.get("preregistration", {}).get("v3_confirmation_plan_is_development_only") is True,
        "v4_plan_development_only": plan.get("preregistration", {}).get("v4_confirmation_plan_is_development_only") is True,
        "strict_ninety_percent_gate": plan.get("gate", {}).get("minimum_success_rate") == 0.9,
        "three_repeats": plan.get("preregistration", {}).get("repeat_count") == 3,
        "ninety_five_percent_repeatability": plan.get("repeatability_gate", {}).get("minimum_status_consistency_rate") == 0.95,
        "expected_v5_checkpoint": plan.get("frozen_controller_contract", {}).get("checkpoint_id") == "rm65_failure_correction_v5_lora_4k/3999",
        "post_control_safety_reporting_required": plan.get(
            "frozen_controller_contract", {}
        ).get("post_control_workspace_safety_checks_required")
        is True
        and plan.get("frozen_controller_contract", {}).get(
            "cube_workspace_escape_radius_m"
        )
        == 1.0,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "validation_kind": "rm65_pi05_failure_correction_v5_confirmation_plan",
        "checks": checks,
        "case_count": len(cases),
        "training_case_count_considered": len(training_cases),
        "prior_evaluation_case_count_considered": len(prior_cases),
        "angles_rad": list(CONFIRMATION_ANGLES_RAD),
        "offsets_m": [list(item) for item in CONFIRMATION_OFFSETS_M],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-evaluation-plan", type=Path, required=True)
    parser.add_argument("--repeatability-report", type=Path, required=True)
    parser.add_argument("--training-plan", type=Path, action="append", default=[])
    parser.add_argument("--exclude-evaluation-plan", type=Path, action="append", default=[])
    parser.add_argument("--policy-seed-start", type=int, default=692029000)
    parser.add_argument("--simulation-seed-start", type=int, default=792029000)
    parser.add_argument("--correction-output", type=Path, required=True)
    parser.add_argument("--confirmation-output", type=Path, required=True)
    parser.add_argument("--validation-output", type=Path, required=True)
    args = parser.parse_args()

    source_plan = json.loads(args.source_evaluation_plan.read_text(encoding="utf-8"))
    repeatability = json.loads(args.repeatability_report.read_text(encoding="utf-8"))
    prior_training = [
        json.loads(path.read_text(encoding="utf-8")) for path in args.training_plan
    ]
    prior_evaluations = [source_plan] + [
        json.loads(path.read_text(encoding="utf-8"))
        for path in args.exclude_evaluation_plan
    ]
    correction = build_correction_plan(source_plan, repeatability)
    correction_validation = validate_correction_plan(correction)
    confirmation = build_confirmation_plan(
        args.policy_seed_start, args.simulation_seed_start
    )
    confirmation_validation = validate_confirmation_plan(
        confirmation, prior_training + [correction], prior_evaluations
    )
    report = {
        "status": (
            "pass"
            if correction_validation["status"] == "pass"
            and confirmation_validation["status"] == "pass"
            else "fail"
        ),
        "correction": correction_validation,
        "confirmation": confirmation_validation,
        "real_robot_command_sent": False,
    }
    for path, value in (
        (args.correction_output, correction),
        (args.confirmation_output, confirmation),
        (args.validation_output, report),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
