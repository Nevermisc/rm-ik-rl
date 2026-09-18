"""Deterministic safety guard for a future seven-value RM65 policy action chunk."""

from __future__ import annotations

import dataclasses

import numpy as np


RM65_LOWER_RAD = np.array([-3.106, -2.2689, -2.356, -3.106, -2.234, -6.28], dtype=np.float32)
RM65_UPPER_RAD = np.array([3.106, 2.2689, 2.356, 3.106, 2.234, 6.28], dtype=np.float32)


@dataclasses.dataclass(frozen=True)
class GuardConfig:
    joint_limit_margin_rad: float = 0.02
    max_joint_step_rad: float = 0.05


def guard_action_chunk(
    actions: np.ndarray,
    current_joint_position: np.ndarray,
    config: GuardConfig = GuardConfig(),
) -> tuple[np.ndarray, dict]:
    """Validate and clamp RM65 absolute joint targets plus normalized gripper targets."""

    source = np.asarray(actions, dtype=np.float32)
    current = np.asarray(current_joint_position, dtype=np.float32)
    if source.ndim != 2 or source.shape[1] != 7:
        raise ValueError(f"expected action shape (T, 7), got {source.shape}")
    if current.shape != (6,):
        raise ValueError(f"expected six current joints, got {current.shape}")
    if not np.isfinite(source).all() or not np.isfinite(current).all():
        raise ValueError("action chunk and current joints must contain only finite values")
    if config.joint_limit_margin_rad < 0 or config.max_joint_step_rad <= 0:
        raise ValueError("guard margins must be non-negative and step limit must be positive")

    lower = RM65_LOWER_RAD + config.joint_limit_margin_rad
    upper = RM65_UPPER_RAD - config.joint_limit_margin_rad
    safe = source.copy()
    joint_limit_clamps = 0
    step_clamps = 0
    previous = np.clip(current, lower, upper)
    for index in range(len(safe)):
        joint_target = np.clip(safe[index, :6], lower, upper)
        joint_limit_clamps += int(np.count_nonzero(joint_target != safe[index, :6]))
        step_lower = previous - config.max_joint_step_rad
        step_upper = previous + config.max_joint_step_rad
        stepped = np.clip(joint_target, step_lower, step_upper)
        step_clamps += int(np.count_nonzero(stepped != joint_target))
        safe[index, :6] = stepped
        safe[index, 6] = np.clip(safe[index, 6], 0.0, 1.0)
        previous = stepped

    diagnostics = {
        "status": "pass",
        "input_shape": list(source.shape),
        "all_finite": True,
        "joint_limit_margin_rad": config.joint_limit_margin_rad,
        "max_joint_step_rad": config.max_joint_step_rad,
        "joint_limit_clamp_count": joint_limit_clamps,
        "joint_step_clamp_count": step_clamps,
        "gripper_clamp_count": int(np.count_nonzero(safe[:, 6] != source[:, 6])),
        "maximum_output_step_rad": float(
            np.max(np.abs(np.diff(np.vstack([current, safe[:, :6]]), axis=0)))
        ),
    }
    return safe, diagnostics
