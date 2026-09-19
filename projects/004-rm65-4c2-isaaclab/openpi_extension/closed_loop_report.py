"""Independent validation for an RM65 pi0.5 closed-loop task report."""

from __future__ import annotations

from typing import Any


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result


def validate_closed_loop_task_report(
    report: dict[str, Any], *, expected_checkpoint_id: str
) -> dict[str, Any]:
    source_distance = _number(report.get("source_to_target_xy_distance_m"))
    lift_height = _number(report.get("block_lift_height_m"))
    xy_error = _number(report.get("final_target_xy_error_m"))
    position_error = _number(report.get("final_target_position_error_m"))
    drift = _number(report.get("post_release_drift_m"))
    final_gripper = _number(report.get("final_gripper_normalized"))
    checks = {
        "status_pass": report.get("status") == "pass",
        "simulation_only": report.get("simulation_only") is True,
        "pi05_used": report.get("pi05_used") is True,
        "real_robot_command_not_sent": report.get("real_robot_command_sent") is False,
        "checkpoint_matches": report.get("policy_checkpoint_id") == expected_checkpoint_id,
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
    }
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "status": "pass" if not failed else "blocked",
        "execution_verified": not failed,
        "expected_checkpoint_id": expected_checkpoint_id,
        "checks": checks,
        "failed_checks": failed,
    }
