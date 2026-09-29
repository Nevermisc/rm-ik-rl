"""Independent validation for an RM65 pi0.5 closed-loop task report."""

from __future__ import annotations

from typing import Any

from openpi_extension.deterministic_policy import (
    POLICY_SAMPLING_MODE,
    policy_sampling_evidence,
)


REQUIRED_OBSERVATION_SHA256_FIELDS = {
    "joint_position",
    "gripper_position",
    "external_image",
    "wrist_image",
}


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result


def _sha256_string(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def build_preflight_safety_failure_report(
    *,
    checkpoint_id: str | None,
    policy_noise_seed: int | None,
    simulation_seed: int,
    prompt: str,
    transfer_joint_1_rad: float,
    source_offset_x_m: float,
    source_offset_y_m: float,
    policy_max_action_chunks: int,
    policy_execute_actions_per_chunk: int,
    record_stride_steps: int,
    policy_release_required_consecutive_chunks: int,
    policy_gripper_open_threshold: float,
    policy_gripper_actual_open_threshold: float,
    python_hash_seed: str | None,
    failure_reason: str,
    failure_message: str,
    pi05_used: bool = True,
    expert: str | None = None,
) -> dict[str, Any]:
    """Create an auditable task failure before any policy action is executed."""

    report = {
        "status": "fail",
        "simulation_only": True,
        "pi05_used": pi05_used,
        "expert": expert,
        "real_robot_command_sent": False,
        "policy_checkpoint_id": checkpoint_id if pi05_used else None,
        "policy_noise_seed": policy_noise_seed if pi05_used else None,
        "simulation_seed": simulation_seed,
        "prompt": prompt,
        "transfer_joint_1_rad": transfer_joint_1_rad,
        "source_offset_xy_m": [source_offset_x_m, source_offset_y_m],
        "action_chunks": 0,
        "executed_actions": 0,
        "controller_config": {
            "policy_max_action_chunks": policy_max_action_chunks,
            "policy_execute_actions_per_chunk": policy_execute_actions_per_chunk,
            "record_stride_steps": record_stride_steps,
            "success_candidate_required_consecutive_chunks": (
                policy_release_required_consecutive_chunks
            ),
            "policy_gripper_open_threshold": policy_gripper_open_threshold,
            "policy_gripper_actual_open_threshold": (
                policy_gripper_actual_open_threshold
            ),
            "target_zone_arm_hold_enabled": True,
            "target_zone_arm_hold_error_m_lt": 0.05,
            "target_zone_execute_full_action_chunk": True,
            "policy_noise_seed": policy_noise_seed,
            "policy_chunk_seed_rule": "case_seed + chunk_index",
            "simulation_seed": simulation_seed,
            "cube_workspace_escape_radius_m": 1.0,
        },
        "simulation_determinism": {
            "seed": simulation_seed,
            "python_hash_seed": python_hash_seed,
            "torch_deterministic_algorithms": True,
            "replicator_global_seed": simulation_seed,
            "physx_enhanced_determinism": True,
            "camera_antialiasing_mode": "FXAA",
            "dlss_frame_generation_enabled": False,
            "dl_denoiser_enabled": False,
            "motion_blur_enabled": False,
            "tv_noise_enabled": False,
        },
        "deterministic_sampling": {
            "mode": POLICY_SAMPLING_MODE,
            "case_seed": policy_noise_seed,
            "chunk_seed_rule": "case_seed + chunk_index",
            "noise_shape": [10, 32],
            "noise_dtype": "float32",
            "server_metadata": None,
            "chunks": [],
        },
        "preflight_failure": {
            "stage": "kinematic_safety_preflight",
            "reason": failure_reason,
            "message": failure_message,
            "policy_inference_started": False,
            "robot_motion_started": False,
        },
        "simulation_safety_abort_reason": failure_reason,
        "release_verification": {
            "verified": False,
            "reason": "preflight_safety_rejection",
        },
        "all_states_finite": True,
        "source_to_target_xy_distance_m": None,
        "block_lift_height_m": None,
        "final_target_xy_error_m": None,
        "final_target_position_error_m": None,
        "post_release_drift_m": None,
        "final_gripper_normalized": None,
        "limitation": "The task was rejected before policy inference or robot motion.",
    }
    if not pi05_used:
        report["controller_config"] = {}
        report["deterministic_sampling"] = None
        report["simulation_determinism"].update(
            {
                "torch_deterministic_algorithms": False,
                "physx_enhanced_determinism": False,
                "camera_antialiasing_mode": None,
                "dlss_frame_generation_enabled": None,
                "dl_denoiser_enabled": None,
                "motion_blur_enabled": None,
                "tv_noise_enabled": None,
            }
        )
        report["scripted_expert_config"] = {
            "record_stride_steps": record_stride_steps,
        }
        report["preflight_failure"]["execution_mode"] = "scripted_expert"
        report["limitation"] = (
            "The scripted expert was rejected before robot motion; no episode "
            "was recorded and the attempt is not training-ready."
        )
    else:
        report["preflight_failure"]["execution_mode"] = "pi05_closed_loop"
    return report


def _deterministic_sampling_valid(
    report: dict[str, Any], expected_policy_noise_seed: int
) -> bool:
    sampling = report.get("deterministic_sampling")
    action_chunks = report.get("action_chunks")
    if not isinstance(sampling, dict) or not isinstance(action_chunks, int):
        return False
    if (
        report.get("policy_noise_seed") != expected_policy_noise_seed
        or sampling.get("mode") != POLICY_SAMPLING_MODE
        or sampling.get("case_seed") != expected_policy_noise_seed
        or sampling.get("chunk_seed_rule") != "case_seed + chunk_index"
        or sampling.get("noise_shape") != [10, 32]
        or sampling.get("noise_dtype") != "float32"
    ):
        return False
    chunks = sampling.get("chunks")
    if not isinstance(chunks, list) or len(chunks) != action_chunks:
        return False
    for chunk_index, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            return False
        chunk_seed = expected_policy_noise_seed + chunk_index
        expected = policy_sampling_evidence(chunk_seed, 10, 32)
        if any(chunk.get(key) != value for key, value in expected.items()):
            return False
        observation_hashes = chunk.get("observation_sha256")
        if (
            chunk.get("chunk_index") != chunk_index
            or not isinstance(observation_hashes, dict)
            or not REQUIRED_OBSERVATION_SHA256_FIELDS.issubset(observation_hashes)
            or not all(_sha256_string(value) for value in observation_hashes.values())
            or chunk.get("raw_action_shape") != [10, 7]
            or chunk.get("raw_action_dtype") != "float32"
            or not _sha256_string(chunk.get("raw_action_sha256"))
            or not isinstance(chunk.get("raw_gripper_targets"), list)
            or len(chunk["raw_gripper_targets"]) != 10
            or not all(_number(value) is not None for value in chunk["raw_gripper_targets"])
            or chunk.get("safe_action_shape") != [10, 7]
            or chunk.get("safe_action_dtype") != "float32"
            or not _sha256_string(chunk.get("safe_action_sha256"))
            or not isinstance(chunk.get("safe_gripper_targets"), list)
            or len(chunk["safe_gripper_targets"]) != 10
            or not all(
                _number(value) is not None and 0.0 <= float(value) <= 1.0
                for value in chunk["safe_gripper_targets"]
            )
            or not isinstance(chunk.get("executed_action_count"), int)
            or chunk["executed_action_count"] <= 0
        ):
            return False
    return True


def _simulation_determinism_valid(
    report: dict[str, Any], expected_simulation_seed: int
) -> bool:
    evidence = report.get("simulation_determinism")
    return bool(
        isinstance(evidence, dict)
        and report.get("simulation_seed") == expected_simulation_seed
        and evidence.get("seed") == expected_simulation_seed
        and evidence.get("python_hash_seed") == str(expected_simulation_seed)
        and evidence.get("torch_deterministic_algorithms") is True
        and evidence.get("replicator_global_seed") == expected_simulation_seed
        and evidence.get("physx_enhanced_determinism") is True
        and evidence.get("camera_antialiasing_mode") == "FXAA"
        and evidence.get("dlss_frame_generation_enabled") is False
        and evidence.get("dl_denoiser_enabled") is False
        and evidence.get("motion_blur_enabled") is False
        and evidence.get("tv_noise_enabled") is False
    )


def validate_closed_loop_task_report(
    report: dict[str, Any],
    *,
    expected_checkpoint_id: str,
    expected_policy_noise_seed: int,
    expected_simulation_seed: int,
) -> dict[str, Any]:
    controller = report.get("controller_config", {})
    source_distance = _number(report.get("source_to_target_xy_distance_m"))
    lift_height = _number(report.get("block_lift_height_m"))
    xy_error = _number(report.get("final_target_xy_error_m"))
    position_error = _number(report.get("final_target_position_error_m"))
    drift = _number(report.get("post_release_drift_m"))
    final_gripper = _number(report.get("final_gripper_normalized"))
    postcondition = report.get("low_level_release_postcondition", {})
    postcondition_applied = postcondition.get("applied")
    postcondition_valid = isinstance(postcondition_applied, bool)
    if postcondition_applied is True:
        arm_target = postcondition.get("arm_target_latched_to_actual_rad")
        postcondition_valid = bool(
            postcondition.get("model_selected_release") is True
            and postcondition.get("gripper_target_normalized") == 0.0
            and isinstance(arm_target, list)
            and len(arm_target) == 6
            and all(_number(value) is not None for value in arm_target)
            and isinstance(postcondition.get("verification_settle_steps"), int)
            and postcondition["verification_settle_steps"] >= 240
        )
    checks = {
        "status_pass": report.get("status") == "pass",
        "simulation_only": report.get("simulation_only") is True,
        "pi05_used": report.get("pi05_used") is True,
        "real_robot_command_not_sent": report.get("real_robot_command_sent") is False,
        "checkpoint_matches": report.get("policy_checkpoint_id") == expected_checkpoint_id,
        "policy_noise_seed_matches": report.get("policy_noise_seed")
        == expected_policy_noise_seed,
        "deterministic_sampling_verified": _deterministic_sampling_valid(
            report, expected_policy_noise_seed
        ),
        "simulation_seed_matches": report.get("simulation_seed")
        == expected_simulation_seed,
        "simulation_determinism_verified": _simulation_determinism_valid(
            report, expected_simulation_seed
        ),
        "release_supervisor_config_verified": bool(
            isinstance(controller, dict)
            and controller.get("policy_max_action_chunks") == 120
            and controller.get("policy_execute_actions_per_chunk") == 5
            and controller.get("success_candidate_required_consecutive_chunks") == 2
            and controller.get("policy_gripper_open_threshold") == 0.12
            and controller.get("policy_gripper_actual_open_threshold") == 0.20
            and controller.get("target_zone_arm_hold_enabled") is True
            and controller.get("target_zone_arm_hold_error_m_lt") == 0.05
            and controller.get("target_zone_execute_full_action_chunk") is True
            and controller.get("cube_workspace_escape_radius_m") == 1.0
        ),
        "action_chunks_positive": isinstance(report.get("action_chunks"), int)
        and report["action_chunks"] > 0,
        "executed_actions_positive": isinstance(report.get("executed_actions"), int)
        and report["executed_actions"] > 0,
        "source_to_target_distance": source_distance is not None and source_distance > 0.12,
        "block_lift_height": lift_height is not None and lift_height > 0.02,
        "final_target_xy_error": xy_error is not None and xy_error < 0.05,
        "final_target_position_error": position_error is not None and position_error < 0.05,
        "post_release_drift": drift is not None and drift < 0.02,
        "final_gripper_open": final_gripper is not None and final_gripper < 0.12,
        "all_states_finite": report.get("all_states_finite") is True,
        "simulation_safety_not_aborted": report.get("simulation_safety_abort_reason")
        is None,
        "episode_validation": report.get("episode", {}).get("validation", {}).get("status")
        == "pass",
        "evaluation_only": report.get("episode", {}).get("evaluation_only") is True,
        "release_postcondition_transparent": postcondition_valid,
    }
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "status": "pass" if not failed else "blocked",
        "execution_verified": not failed,
        "expected_checkpoint_id": expected_checkpoint_id,
        "expected_policy_noise_seed": expected_policy_noise_seed,
        "expected_simulation_seed": expected_simulation_seed,
        "checks": checks,
        "failed_checks": failed,
    }
