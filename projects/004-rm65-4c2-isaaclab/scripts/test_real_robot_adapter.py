#!/usr/bin/env python3
"""Test side-effect-free RM65 ROS2 and gripper adapters."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openpi_extension.real_robot_adapter import (
    extract_ordered_joint_positions,
    guard_real_robot_action_chunk,
    normalized_gripper_to_driver_position,
    validate_gripper_calibration,
)


def must_raise(callback) -> None:
    try:
        callback()
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def main() -> int:
    names = ["joint3", "joint1", "joint6", "joint2", "joint5", "joint4"]
    positions = [0.3, 0.1, 0.6, 0.2, 0.5, 0.4]
    ordered = extract_ordered_joint_positions(names, positions)
    np.testing.assert_allclose(ordered, [0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
    must_raise(lambda: extract_ordered_joint_positions(["joint1"], [0.0]))

    calibration = {
        "format": "rm65_4c2_gripper_calibration_v1",
        "verified": True,
        "command_open": 950,
        "command_closed": 120,
        "measured_open_width_mm": 68.0,
        "measured_closed_width_mm": 4.0,
    }
    assert validate_gripper_calibration(calibration)["status"] == "pass"
    assert normalized_gripper_to_driver_position(0.0, calibration) == 950
    assert normalized_gripper_to_driver_position(1.0, calibration) == 120
    assert normalized_gripper_to_driver_position(0.5, calibration) == 535
    blocked = dict(calibration, verified=False)
    must_raise(lambda: normalized_gripper_to_driver_position(0.5, blocked))

    current = np.zeros(6, dtype=np.float32)
    actions = np.array([[1.0, -1.0, 0.2, -0.2, 0.1, -0.1, 1.2]], dtype=np.float32)
    safe, guard = guard_real_robot_action_chunk(actions, current)
    assert float(np.max(np.abs(safe[0, :6] - current))) <= 0.0100001
    assert safe[0, 6] == 1.0
    assert guard["joint_step_clamp_count"] == 6
    assert guard["gripper_clamp_count"] == 1

    print(
        json.dumps(
            {
                "status": "pass",
                "side_effects": False,
                "joint_order": ordered.tolist(),
                "open_command": normalized_gripper_to_driver_position(0.0, calibration),
                "closed_command": normalized_gripper_to_driver_position(1.0, calibration),
                "maximum_real_robot_step_rad": guard["maximum_output_step_rad"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
