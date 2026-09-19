#!/usr/bin/env python3
"""Test the side-effect-free core of the RM65 shadow runtime."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openpi_extension.shadow_runtime import (  # noqa: E402
    ShadowFreshnessConfig,
    build_shadow_observation,
    decode_ros_rgb_image,
    validate_shadow_records,
)


def must_raise(callback) -> None:
    try:
        callback()
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def main() -> int:
    # Two BGR pixels plus two padding bytes exercise row-step handling.
    message = SimpleNamespace(
        height=1,
        width=2,
        step=8,
        encoding="bgr8",
        data=bytes([1, 2, 3, 4, 5, 6, 99, 99]),
    )
    decoded = decode_ros_rgb_image(message)
    np.testing.assert_array_equal(decoded, [[[3, 2, 1], [6, 5, 4]]])

    names = ["joint3", "joint1", "joint6", "joint2", "joint5", "joint4"]
    positions = [0.3, 0.1, 0.6, 0.2, 0.5, 0.4]
    image = np.zeros((4, 5, 3), dtype=np.uint8)
    kwargs = dict(
        joint_names=names,
        joint_positions=positions,
        external_rgb=image,
        wrist_rgb=image.copy(),
        joint_timestamp=9.91,
        external_timestamp=9.94,
        wrist_timestamp=9.96,
        now=10.0,
        gripper_normalized=0.0,
        prompt="pick up the block",
        config=ShadowFreshnessConfig(max_age_seconds=0.25, max_skew_seconds=0.10),
    )
    observation, report = build_shadow_observation(**kwargs)
    np.testing.assert_allclose(
        observation["observation/joint_position"], [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
    )
    assert report["sensor_skew_seconds"] <= 0.0500001
    assert report["gripper_state_source"] == "operator_confirmed_static_value"
    must_raise(lambda: build_shadow_observation(**dict(kwargs, joint_timestamp=9.0)))
    must_raise(lambda: build_shadow_observation(**dict(kwargs, wrist_timestamp=9.7)))
    must_raise(lambda: build_shadow_observation(**dict(kwargs, gripper_normalized=1.1)))

    good_record = {
        "status": "pass",
        "mode": "read_only_policy_shadow",
        "real_robot_command_sent": False,
        "ros_publishers_created": 0,
        "sensor": {
            "joint_age_seconds": 0.09,
            "external_image_age_seconds": 0.06,
            "wrist_image_age_seconds": 0.04,
            "sensor_skew_seconds": 0.05,
        },
        "image_sha256": {"external": "a" * 64, "wrist": "b" * 64},
        "predicted_action_shape": [10, 7],
        "first_predicted_action": [0.0] * 7,
        "first_guarded_action": [0.0] * 7,
        "driver_stream": {
            "point_count": 25,
            "duration_seconds": 0.5,
            "maximum_joint_step_rad": 0.004,
        },
    }
    good_records = [dict(good_record, sample_index=index) for index in range(20)]
    validation = validate_shadow_records(good_records)
    assert validation["policy_shadow_passed"] is True
    unsafe_records = [dict(record) for record in good_records]
    unsafe_records[3] = dict(unsafe_records[3], real_robot_command_sent=True)
    assert validate_shadow_records(unsafe_records)["policy_shadow_passed"] is False
    malformed_records = [dict(record) for record in good_records]
    malformed_records[4] = dict(malformed_records[4], driver_stream={"point_count": 25})
    assert validate_shadow_records(malformed_records)["policy_shadow_passed"] is False

    shadow_script = PROJECT_ROOT / "scripts" / "run_rm65_policy_shadow.py"
    source = shadow_script.read_text(encoding="utf-8")
    assert "create_publisher" not in source
    assert "rm_ros_interfaces" not in source
    print(
        json.dumps(
            {
                "status": "pass",
                "read_only": True,
                "ros_publishers_created": 0,
                "decoded_pixel_0_rgb": decoded[0, 0].tolist(),
                "sensor_skew_seconds": report["sensor_skew_seconds"],
                "gripper_state_source": report["gripper_state_source"],
                "twenty_sample_validation": validation["status"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
