#!/usr/bin/env python3
"""Validate the frozen RM65 v5 training and evaluation contract before inference."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_REPO_ID = "local/rm65_sim_failure_correction_v5_train"
EXPECTED_TRAINING = {
    "status": "pass",
    "simulation_only": True,
    "real_robot_command_sent": False,
    "config_name": "pi05_rm65_lora",
    "repo_id": EXPECTED_REPO_ID,
    "exp_name": "rm65_failure_correction_v5_lora_4k",
    "batch_size": 1,
    "num_train_steps": 4000,
    "warmup_steps": 200,
    "peak_lr": 1e-6,
    "decay_lr": 2.5e-7,
    "keep_period": 2000,
}


def validate_evaluation_preflight(
    *,
    training: dict[str, Any],
    training_gate: dict[str, Any],
    norm: dict[str, Any],
    plan: dict[str, Any],
    plans_validation: dict[str, Any],
    checkpoint_path: Path,
    norm_asset: Path,
) -> dict[str, Any]:
    checkpoint_id = f"{checkpoint_path.parent.name}/{checkpoint_path.name}"
    controller = plan.get("frozen_controller_contract", {})
    preregistration = plan.get("preregistration", {})
    gate = plan.get("gate", {})
    repeatability = plan.get("repeatability_gate", {})
    confirmation_validation = plans_validation.get("confirmation", {})
    training_contract = training_gate.get("training_contract", {})
    expected_training_contract = {
        "repo_id": EXPECTED_REPO_ID,
        "episode_count": 150,
        "initial_checkpoint": "rm65_failure_correction_v4_lora_6k/5999/params",
        "target_checkpoint": "rm65_failure_correction_v5_lora_4k/3999",
        "num_train_steps": 4000,
        "batch_size": 1,
        "warmup_steps": 200,
        "peak_lr": 1e-6,
        "decay_lr": 2.5e-7,
        "save_interval": 2000,
        "keep_period": 2000,
    }
    declared_norm_path = Path(norm.get("output_path", "")).expanduser().resolve()
    actual_norm_hash = (
        hashlib.sha256(norm_asset.read_bytes()).hexdigest()
        if norm_asset.is_file()
        else None
    )
    checks = {
        **{
            f"training_{key}": training.get(key) == expected
            for key, expected in EXPECTED_TRAINING.items()
        },
        "training_gate_pass": training_gate.get("status") == "pass",
        "training_gate_checks_all_pass": bool(training_gate.get("checks"))
        and all(training_gate.get("checks", {}).values()),
        "training_gate_contract": all(
            training_contract.get(key) == expected
            for key, expected in expected_training_contract.items()
        ),
        "latest_checkpoint_matches": Path(training.get("latest_checkpoint", "")).resolve()
        == checkpoint_path,
        "checkpoint_exists": checkpoint_path.is_dir(),
        "checkpoint_id_frozen": checkpoint_id
        == "rm65_failure_correction_v5_lora_4k/3999"
        == controller.get("checkpoint_id"),
        "controller_repo_id": controller.get("repo_id") == EXPECTED_REPO_ID,
        "norm_report_pass": norm.get("status") == "pass",
        "norm_repo_id": norm.get("repo_id") == EXPECTED_REPO_ID,
        "norm_processed_frames": isinstance(norm.get("processed_frames"), int)
        and norm.get("processed_frames", 0) > 0,
        "norm_keys": set(norm.get("keys", [])) == {"actions", "state"},
        "norm_asset_exists": norm_asset.is_file(),
        "norm_asset_path_matches": declared_norm_path == norm_asset,
        "norm_asset_hash_matches": actual_norm_hash == norm.get("sha256"),
        "plans_validation_pass": plans_validation.get("status") == "pass",
        "confirmation_validation_pass": confirmation_validation.get("status") == "pass",
        "confirmation_checks_all_pass": bool(confirmation_validation.get("checks"))
        and all(confirmation_validation.get("checks", {}).values()),
        "plan_format": plan.get("format")
        == "rm65_pi05_sim_evaluation_plan_deterministic_v1",
        "twenty_cases": len(plan.get("cases", [])) == 20,
        "created_before_v5_training": preregistration.get("created_before_v5_training")
        is True,
        "three_repeats": preregistration.get("repeat_count") == 3,
        "first_run_independent": preregistration.get(
            "first_run_is_independent_success_confirmation"
        )
        is True,
        "later_runs_repeatability_only": preregistration.get(
            "later_runs_are_repeatability_evidence_not_new_success_trials"
        )
        is True,
        "normal_failures_not_retried": preregistration.get(
            "normal_model_failures_must_not_be_retried"
        )
        is True,
        "infrastructure_retry_only": preregistration.get(
            "infrastructure_retries_require_missing_valid_report"
        )
        is True,
        "confirmation_not_in_training": preregistration.get(
            "conditions_must_not_be_added_to_training_before_confirmation"
        )
        is True,
        "v3_v4_plans_development_only": preregistration.get(
            "v3_confirmation_plan_is_development_only"
        )
        is True
        and preregistration.get("v4_confirmation_plan_is_development_only") is True,
        "strict_success_gate": gate.get("minimum_episode_count") == 20
        and gate.get("minimum_success_rate") == 0.9
        and gate.get("require_all_planned_reports") is True,
        "controller_thresholds": controller.get("policy_max_action_chunks") == 120
        and controller.get("policy_gripper_open_threshold") == 0.12
        and controller.get("actual_gripper_open_threshold") == 0.20
        and controller.get("required_release_candidate_chunks") == 2,
        "post_control_workspace_safety_required": controller.get(
            "post_control_workspace_safety_checks_required"
        )
        is True
        and controller.get("cube_workspace_escape_radius_m") == 1.0,
        "repeatability_contract": repeatability.get("required_reports") == 60
        and repeatability.get("minimum_status_consistency_rate") == 0.95
        and repeatability.get("maximum_outcome_flip_cases") == 1
        and repeatability.get("require_initial_joint_hash_match") is True
        and repeatability.get("require_initial_gripper_hash_match") is True
        and repeatability.get("require_chunk_zero_noise_hash_match") is True,
    }
    return {
        "schema": "rm65_pi05_failure_correction_v5_evaluation_preflight_v1",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "checkpoint": str(checkpoint_path),
        "checkpoint_id": checkpoint_id,
        "repo_id": EXPECTED_REPO_ID,
        "norm_asset": str(norm_asset),
        "norm_sha256": actual_norm_hash,
        "simulation_only": True,
        "real_robot_command_sent": False,
    }


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training-report", type=Path, required=True)
    parser.add_argument("--training-gate", type=Path, required=True)
    parser.add_argument("--norm-report", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--plans-validation", type=Path, required=True)
    parser.add_argument("--norm-asset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    training = load(args.training_report)
    checkpoint = Path(training.get("latest_checkpoint", "")).expanduser().resolve()
    report = validate_evaluation_preflight(
        training=training,
        training_gate=load(args.training_gate),
        norm=load(args.norm_report),
        plan=load(args.plan),
        plans_validation=load(args.plans_validation),
        checkpoint_path=checkpoint,
        norm_asset=args.norm_asset.expanduser().resolve(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if report["status"] != "pass":
        failed = [name for name, passed in report["checks"].items() if not passed]
        raise SystemExit(f"v5 evaluation preflight failed: {failed}")
    print(report["checkpoint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
