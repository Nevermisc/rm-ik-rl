"""Pure, side-effect-free adapters for a future RM65 + 4C2 ROS2 bridge."""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from openpi_extension.action_guard import GuardConfig, guard_action_chunk


RM65_ROS_JOINT_NAMES = tuple(f"joint{index}" for index in range(1, 7))
GRIPPER_CALIBRATION_FORMAT = "rm65_4c2_gripper_calibration_v1"


def extract_ordered_joint_positions(
    names: Sequence[str], positions: Sequence[float]
) -> np.ndarray:
    """Return RM65 joints in driver order and reject missing/duplicate names."""

    if len(names) != len(positions):
        raise ValueError("joint names and positions must have equal length")
    if len(set(names)) != len(names):
        raise ValueError("joint names must be unique")
    mapping = dict(zip(names, positions, strict=True))
    missing = [name for name in RM65_ROS_JOINT_NAMES if name not in mapping]
    if missing:
        raise ValueError(f"missing RM65 joints: {missing}")
    ordered = np.asarray([mapping[name] for name in RM65_ROS_JOINT_NAMES], dtype=np.float32)
    if not np.isfinite(ordered).all():
        raise ValueError("joint feedback must contain only finite values")
    return ordered


def validate_gripper_calibration(calibration: dict[str, Any]) -> dict[str, Any]:
    """Validate an explicitly measured 4C2 command mapping."""

    checks = {
        "format": calibration.get("format") == GRIPPER_CALIBRATION_FORMAT,
        "verified": calibration.get("verified") is True,
        "command_open_in_range": isinstance(calibration.get("command_open"), int)
        and 1 <= calibration["command_open"] <= 1000,
        "command_closed_in_range": isinstance(calibration.get("command_closed"), int)
        and 1 <= calibration["command_closed"] <= 1000,
        "commands_distinct": calibration.get("command_open")
        != calibration.get("command_closed"),
        "open_width_positive": isinstance(
            calibration.get("measured_open_width_mm"), (int, float)
        )
        and calibration["measured_open_width_mm"] > 0,
        "closed_width_nonnegative": isinstance(
            calibration.get("measured_closed_width_mm"), (int, float)
        )
        and calibration["measured_closed_width_mm"] >= 0,
        "open_wider_than_closed": isinstance(
            calibration.get("measured_open_width_mm"), (int, float)
        )
        and isinstance(calibration.get("measured_closed_width_mm"), (int, float))
        and calibration["measured_open_width_mm"]
        > calibration["measured_closed_width_mm"],
    }
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "status": "pass" if not failed else "blocked",
        "mapping_allowed": not failed,
        "checks": checks,
        "failed_checks": failed,
    }


def normalized_gripper_to_driver_position(
    normalized_closed: float, calibration: dict[str, Any]
) -> int:
    """Map 0=open and 1=closed only after explicit physical calibration."""

    report = validate_gripper_calibration(calibration)
    if not report["mapping_allowed"]:
        raise ValueError(f"gripper calibration is blocked: {report['failed_checks']}")
    normalized = float(normalized_closed)
    if not np.isfinite(normalized) or not 0.0 <= normalized <= 1.0:
        raise ValueError("normalized gripper command must be finite and inside [0, 1]")
    command_open = calibration["command_open"]
    command_closed = calibration["command_closed"]
    return int(round(command_open + normalized * (command_closed - command_open)))


def guard_real_robot_action_chunk(
    actions: np.ndarray, current_joint_position: np.ndarray
) -> tuple[np.ndarray, dict]:
    """Apply a stricter first-deployment step limit than simulation uses."""

    return guard_action_chunk(
        actions,
        current_joint_position,
        GuardConfig(joint_limit_margin_rad=0.05, max_joint_step_rad=0.01),
    )
