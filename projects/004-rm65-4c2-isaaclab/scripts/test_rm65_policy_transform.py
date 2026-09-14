#!/usr/bin/env python3
"""Unit-check the future RM65 OpenPI transform with synthetic observations."""

from __future__ import annotations

import json

import numpy as np

from openpi.models import model as _model
from openpi_extension.rm65_policy import RM65Inputs, RM65Outputs


def main() -> None:
    source = {
        "observation/external_image": np.zeros((480, 640, 3), dtype=np.uint8),
        "observation/wrist_image": np.ones((3, 480, 640), dtype=np.float32),
        "observation/joint_position": np.arange(6, dtype=np.float32) / 10,
        "observation/gripper_position": np.float32(0.25),
        "actions": np.zeros((16, 7), dtype=np.float32),
        "prompt": b"pick up the red cube",
    }
    transformed = RM65Inputs(model_type=_model.ModelType.PI05)(source)
    decoded = RM65Outputs()({"actions": np.zeros((16, 32), dtype=np.float32)})
    checks = {
        "state_shape": list(transformed["state"].shape),
        "state_dtype": str(transformed["state"].dtype),
        "action_input_shape": list(transformed["actions"].shape),
        "action_output_shape": list(decoded["actions"].shape),
        "base_image_shape": list(transformed["image"]["base_0_rgb"].shape),
        "wrist_image_shape": list(transformed["image"]["left_wrist_0_rgb"].shape),
        "right_wrist_mask": bool(transformed["image_mask"]["right_wrist_0_rgb"]),
        "prompt": transformed["prompt"],
    }
    expected = {
        "state_shape": [7],
        "action_input_shape": [16, 7],
        "action_output_shape": [16, 7],
        "base_image_shape": [480, 640, 3],
        "wrist_image_shape": [480, 640, 3],
        "right_wrist_mask": False,
        "prompt": "pick up the red cube",
    }
    for key, value in expected.items():
        if checks[key] != value:
            raise AssertionError(f"{key}: expected {value!r}, got {checks[key]!r}")
    checks["status"] = "pass"
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
