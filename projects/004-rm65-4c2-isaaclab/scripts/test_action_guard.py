#!/usr/bin/env python3
"""Check RM65 action guard limits, step clamps, gripper clamps, and NaN rejection."""

from __future__ import annotations

import json

import numpy as np

from openpi_extension.action_guard import GuardConfig, guard_action_chunk


def main() -> None:
    current = np.zeros(6, dtype=np.float32)
    source = np.array(
        [
            [10.0, -10.0, 1.0, 0.0, 0.0, 0.0, -2.0],
            [10.0, -10.0, 1.0, 0.0, 0.0, 0.0, 3.0],
        ],
        dtype=np.float32,
    )
    safe, report = guard_action_chunk(source, current, GuardConfig(max_joint_step_rad=0.05))
    if not np.isfinite(safe).all():
        raise AssertionError("guard produced non-finite values")
    if np.max(np.abs(np.diff(np.vstack([current, safe[:, :6]]), axis=0))) > 0.050001:
        raise AssertionError("joint step clamp failed")
    if not np.array_equal(safe[:, 6], np.array([0.0, 1.0], dtype=np.float32)):
        raise AssertionError("gripper clamp failed")
    rejected_nan = False
    try:
        invalid = source.copy()
        invalid[0, 0] = np.nan
        guard_action_chunk(invalid, current)
    except ValueError:
        rejected_nan = True
    if not rejected_nan:
        raise AssertionError("NaN action was not rejected")
    report["nan_rejected"] = rejected_nan
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
