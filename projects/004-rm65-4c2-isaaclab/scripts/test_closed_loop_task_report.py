#!/usr/bin/env python3
"""Test independent closed-loop report validation."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openpi_extension.closed_loop_report import (
    build_preflight_safety_failure_report,
    validate_closed_loop_task_report,
)
from openpi_extension.deterministic_policy import policy_sampling_evidence


def main() -> int:
    checkpoint_id = "rm65_scripted_v1_lora_30k/29999"
    policy_noise_seed = 8000
    simulation_seed = 7000
    chunks = []
    for chunk_index in range(12):
        chunks.append(
            {
                "chunk_index": chunk_index,
                **policy_sampling_evidence(policy_noise_seed + chunk_index, 10, 32),
                "observation_sha256": {
                    "joint_position": "3" * 64,
                    "gripper_position": "4" * 64,
                    "external_image": "5" * 64,
                    "wrist_image": "6" * 64,
                    "cube_position": "7" * 64,
                },
                "raw_action_shape": [10, 7],
                "raw_action_dtype": "float32",
                "raw_action_sha256": "1" * 64,
                "raw_gripper_targets": [0.5] * 10,
                "safe_action_shape": [10, 7],
                "safe_action_dtype": "float32",
                "safe_action_sha256": "2" * 64,
                "safe_gripper_targets": [0.5] * 10,
                "executed_action_count": 5,
            }
        )
    report = {
        "status": "pass",
        "simulation_only": True,
        "pi05_used": True,
        "real_robot_command_sent": False,
        "policy_checkpoint_id": checkpoint_id,
        "policy_noise_seed": policy_noise_seed,
        "simulation_seed": simulation_seed,
        "action_chunks": 12,
        "executed_actions": 120,
        "controller_config": {
            "policy_max_action_chunks": 120,
            "policy_execute_actions_per_chunk": 5,
            "success_candidate_required_consecutive_chunks": 2,
            "policy_gripper_open_threshold": 0.12,
            "policy_gripper_actual_open_threshold": 0.20,
            "target_zone_arm_hold_enabled": True,
            "target_zone_arm_hold_error_m_lt": 0.05,
            "target_zone_execute_full_action_chunk": True,
            "cube_workspace_escape_radius_m": 1.0,
        },
        "source_to_target_xy_distance_m": 0.2,
        "block_lift_height_m": 0.04,
        "final_target_xy_error_m": 0.01,
        "final_target_position_error_m": 0.02,
        "post_release_drift_m": 0.001,
        "final_gripper_normalized": 0.0,
        "all_states_finite": True,
        "simulation_safety_abort_reason": None,
        "episode": {"validation": {"status": "pass"}, "evaluation_only": True},
        "low_level_release_postcondition": {
            "applied": True,
            "arm_target_latched_to_actual_rad": [0.0] * 6,
            "gripper_target_normalized": 0.0,
            "verification_settle_steps": 240,
            "model_selected_release": True,
        },
        "deterministic_sampling": {
            "mode": "explicit_numpy_gaussian_noise_v1",
            "case_seed": policy_noise_seed,
            "chunk_seed_rule": "case_seed + chunk_index",
            "noise_shape": [10, 32],
            "noise_dtype": "float32",
            "chunks": chunks,
        },
        "simulation_determinism": {
            "seed": simulation_seed,
            "python_hash_seed": str(simulation_seed),
            "torch_deterministic_algorithms": True,
            "replicator_global_seed": simulation_seed,
            "physx_enhanced_determinism": True,
            "camera_antialiasing_mode": "FXAA",
            "dlss_frame_generation_enabled": False,
            "dl_denoiser_enabled": False,
            "motion_blur_enabled": False,
            "tv_noise_enabled": False,
        },
    }
    assert validate_closed_loop_task_report(
        report,
        expected_checkpoint_id=checkpoint_id,
        expected_policy_noise_seed=policy_noise_seed,
        expected_simulation_seed=simulation_seed,
    )["status"] == "pass"
    wrong_checkpoint = dict(report, policy_checkpoint_id="other/1")
    assert validate_closed_loop_task_report(
        wrong_checkpoint,
        expected_checkpoint_id=checkpoint_id,
        expected_policy_noise_seed=policy_noise_seed,
        expected_simulation_seed=simulation_seed,
    )["status"] == "blocked"
    false_status = dict(report, status="fail")
    assert validate_closed_loop_task_report(
        false_status,
        expected_checkpoint_id=checkpoint_id,
        expected_policy_noise_seed=policy_noise_seed,
        expected_simulation_seed=simulation_seed,
    )["status"] == "blocked"
    incomplete = dict(report)
    incomplete.pop("executed_actions")
    assert validate_closed_loop_task_report(
        incomplete,
        expected_checkpoint_id=checkpoint_id,
        expected_policy_noise_seed=policy_noise_seed,
        expected_simulation_seed=simulation_seed,
    )["status"] == "blocked"
    wrong_seed = dict(report, policy_noise_seed=policy_noise_seed + 1)
    assert validate_closed_loop_task_report(
        wrong_seed,
        expected_checkpoint_id=checkpoint_id,
        expected_policy_noise_seed=policy_noise_seed,
        expected_simulation_seed=simulation_seed,
    )["status"] == "blocked"
    wrong_simulation_seed = dict(report, simulation_seed=simulation_seed + 1)
    assert validate_closed_loop_task_report(
        wrong_simulation_seed,
        expected_checkpoint_id=checkpoint_id,
        expected_policy_noise_seed=policy_noise_seed,
        expected_simulation_seed=simulation_seed,
    )["status"] == "blocked"
    tampered_sampling = dict(report)
    tampered_chunks = [dict(chunk) for chunk in chunks]
    tampered_chunks[0]["noise_sha256"] = "0" * 64
    tampered_sampling["deterministic_sampling"] = dict(
        report["deterministic_sampling"], chunks=tampered_chunks
    )
    assert validate_closed_loop_task_report(
        tampered_sampling,
        expected_checkpoint_id=checkpoint_id,
        expected_policy_noise_seed=policy_noise_seed,
        expected_simulation_seed=simulation_seed,
    )["status"] == "blocked"
    safety_aborted = dict(
        report, simulation_safety_abort_reason="cube_outside_workspace_envelope"
    )
    assert validate_closed_loop_task_report(
        safety_aborted,
        expected_checkpoint_id=checkpoint_id,
        expected_policy_noise_seed=policy_noise_seed,
        expected_simulation_seed=simulation_seed,
    )["status"] == "blocked"
    preflight_failure = build_preflight_safety_failure_report(
        checkpoint_id=checkpoint_id,
        policy_noise_seed=policy_noise_seed,
        simulation_seed=simulation_seed,
        prompt="pick up the block",
        transfer_joint_1_rad=0.8,
        source_offset_x_m=0.002,
        source_offset_y_m=-0.003,
        policy_max_action_chunks=120,
        policy_execute_actions_per_chunk=5,
        record_stride_steps=12,
        policy_release_required_consecutive_chunks=2,
        policy_gripper_open_threshold=0.12,
        policy_gripper_actual_open_threshold=0.20,
        python_hash_seed=str(simulation_seed),
        failure_reason="unsafe_ik_branch_jump",
        failure_message="unsafe IK branch jump",
    )
    assert preflight_failure["status"] == "fail"
    assert preflight_failure["transfer_joint_1_rad"] == 0.8
    assert preflight_failure["source_offset_xy_m"] == [0.002, -0.003]
    assert preflight_failure["action_chunks"] == 0
    assert preflight_failure["preflight_failure"]["policy_inference_started"] is False
    assert validate_closed_loop_task_report(
        preflight_failure,
        expected_checkpoint_id=checkpoint_id,
        expected_policy_noise_seed=policy_noise_seed,
        expected_simulation_seed=simulation_seed,
    )["status"] == "blocked"
    scripted_preflight_failure = build_preflight_safety_failure_report(
        checkpoint_id="unknown",
        policy_noise_seed=None,
        simulation_seed=simulation_seed,
        prompt="move the block",
        transfer_joint_1_rad=0.8,
        source_offset_x_m=0.002,
        source_offset_y_m=-0.003,
        policy_max_action_chunks=120,
        policy_execute_actions_per_chunk=5,
        record_stride_steps=12,
        policy_release_required_consecutive_chunks=2,
        policy_gripper_open_threshold=0.12,
        policy_gripper_actual_open_threshold=0.20,
        python_hash_seed=None,
        failure_reason="unsafe_ik_branch_jump",
        failure_message="unsafe IK branch jump",
        pi05_used=False,
        expert="scripted expert",
    )
    assert scripted_preflight_failure["pi05_used"] is False
    assert scripted_preflight_failure["expert"] == "scripted expert"
    assert scripted_preflight_failure["policy_checkpoint_id"] is None
    assert scripted_preflight_failure["deterministic_sampling"] is None
    assert (
        scripted_preflight_failure["preflight_failure"]["execution_mode"]
        == "scripted_expert"
    )
    print(
        json.dumps(
            {
                "status": "pass",
                "wrong_checkpoint_blocked": True,
                "failed_task_blocked": True,
                "missing_execution_evidence_blocked": True,
                "wrong_policy_noise_seed_blocked": True,
                "wrong_simulation_seed_blocked": True,
                "tampered_noise_hash_blocked": True,
                "simulation_safety_abort_blocked": True,
                "preflight_safety_failure_structured_and_blocked": True,
                "scripted_preflight_mode_labeled_correctly": True,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
