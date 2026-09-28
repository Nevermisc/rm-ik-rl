"""Independent validation for an RM65 pi0.5 closed-loop task report."""

from __future__ import annotations

from typing import Any

from openpi_extension.deterministic_policy import (
    POLICY_SAMPLING_MODE,
    policy_sampling_evidence,
)


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
        if (
            chunk.get("chunk_index") != chunk_index
            or chunk.get("raw_action_shape") != [10, 7]
            or chunk.get("raw_action_dtype") != "float32"
            or not _sha256_string(chunk.get("raw_action_sha256"))
            or chunk.get("safe_action_shape") != [10, 7]
            or chunk.get("safe_action_dtype") != "float32"
            or not _sha256_string(chunk.get("safe_action_sha256"))
            or not isinstance(chunk.get("executed_action_count"), int)
            or chunk["executed_action_count"] <= 0
        ):
            return False
    return True


def validate_closed_loop_task_report(
    report: dict[str, Any], *, expected_checkpoint_id: str, expected_policy_noise_seed: int
) -> dict[str, Any]:
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
        "checks": checks,
        "failed_checks": failed,
    }
