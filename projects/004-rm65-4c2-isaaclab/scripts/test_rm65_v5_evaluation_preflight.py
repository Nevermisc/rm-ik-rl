#!/usr/bin/env python3
"""Unit-check the frozen RM65 v5 evaluation preflight contract."""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

from check_rm65_v5_evaluation_preflight import (
    EXPECTED_REPO_ID,
    EXPECTED_TRAINING,
    validate_evaluation_preflight,
)


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        checkpoint = root / "rm65_failure_correction_v5_lora_4k" / "3999"
        checkpoint.mkdir(parents=True)
        norm_asset = root / "norm_stats.json"
        norm_asset.write_text("{}\n", encoding="utf-8")
        training = {
            **EXPECTED_TRAINING,
            "latest_checkpoint": str(checkpoint),
        }
        training_gate = {
            "status": "pass",
            "checks": {"all": True},
            "training_contract": {
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
            },
        }
        norm = {
            "status": "pass",
            "repo_id": EXPECTED_REPO_ID,
            "processed_frames": 10,
            "keys": ["actions", "state"],
            "output_path": str(norm_asset),
            "sha256": hashlib.sha256(norm_asset.read_bytes()).hexdigest(),
        }
        plan = {
            "format": "rm65_pi05_sim_evaluation_plan_deterministic_v1",
            "preregistration": {
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
            "frozen_controller_contract": {
                "checkpoint_id": "rm65_failure_correction_v5_lora_4k/3999",
                "repo_id": EXPECTED_REPO_ID,
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
            },
            "cases": [{"case_id": f"confirm_v5_{index:03d}"} for index in range(20)],
        }
        plans_validation = {
            "status": "pass",
            "confirmation": {"status": "pass", "checks": {"all": True}},
        }
        healthy = validate_evaluation_preflight(
            training=training,
            training_gate=training_gate,
            norm=norm,
            plan=plan,
            plans_validation=plans_validation,
            checkpoint_path=checkpoint.resolve(),
            norm_asset=norm_asset.resolve(),
        )
        drifted_plan = dict(plan)
        drifted_plan["frozen_controller_contract"] = dict(
            plan["frozen_controller_contract"],
            post_control_workspace_safety_checks_required=False,
        )
        rejected = validate_evaluation_preflight(
            training=training,
            training_gate=training_gate,
            norm=norm,
            plan=drifted_plan,
            plans_validation=plans_validation,
            checkpoint_path=checkpoint.resolve(),
            norm_asset=norm_asset.resolve(),
        )
    passed = bool(
        healthy["status"] == "pass"
        and rejected["status"] == "fail"
        and rejected["checks"]["post_control_workspace_safety_required"] is False
    )
    print(f"RM65_V5_EVALUATION_PREFLIGHT={'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
