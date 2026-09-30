"""Keep approach preshape separate from a fully open release target."""
import numpy as np


def gripper_stage_targets(current_targets, close_rad):
    current = np.asarray(current_targets, dtype=np.float64)
    if current.ndim != 1 or current.size == 0 or not np.isfinite(current).all():
        raise ValueError('finite one-dimensional gripper targets required')
    if not np.isfinite(close_rad) or not 0 < close_rad <= 1:
        raise ValueError('invalid close target')
    if np.any(current < 0) or np.any(current > close_rad):
        raise ValueError('approach target outside open/close interval')
    return current.copy(), np.full_like(current, close_rad), np.zeros_like(current)
