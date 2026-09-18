#!/usr/bin/env python3
"""Pure NumPy helpers for deriving RM65 grasp poses."""

from __future__ import annotations

import numpy as np


def interpolate_rotation_matrix(
    start_rotation: np.ndarray,
    target_rotation: np.ndarray,
    fraction: float,
) -> np.ndarray:
    """Interpolate two rotation matrices along their relative axis-angle."""

    if not 0.0 <= fraction <= 1.0:
        raise ValueError("rotation interpolation fraction must be between 0 and 1")
    start = np.asarray(start_rotation, dtype=np.float64)
    target = np.asarray(target_rotation, dtype=np.float64)
    relative = target @ start.T
    cosine = np.clip((np.trace(relative) - 1.0) / 2.0, -1.0, 1.0)
    angle = float(np.arccos(cosine))
    if angle < 1e-10:
        return start.copy()
    if abs(np.sin(angle)) < 1e-8:
        raise ValueError("rotation interpolation is ambiguous at 180 degrees")
    axis = np.array(
        [
            relative[2, 1] - relative[1, 2],
            relative[0, 2] - relative[2, 0],
            relative[1, 0] - relative[0, 1],
        ],
        dtype=np.float64,
    ) / (2.0 * np.sin(angle))
    skew = np.array(
        [
            [0.0, -axis[2], axis[1]],
            [axis[2], 0.0, -axis[0]],
            [-axis[1], axis[0], 0.0],
        ],
        dtype=np.float64,
    )
    partial_angle = fraction * angle
    partial = (
        np.eye(3)
        + np.sin(partial_angle) * skew
        + (1.0 - np.cos(partial_angle)) * (skew @ skew)
    )
    return partial @ start


def compute_top_down_link_pose(
    reference_link_position: np.ndarray,
    reference_link_rotation: np.ndarray,
    block_position: np.ndarray,
    yaw_rad: float,
    tilt_rad: float = 0.0,
    blend_fraction: float = 1.0,
    reference_closing_axis_world: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Rotate a calibrated link-to-block transform into an above-table grasp.

    The reference pose already aligns the gripper pads with the block. This
    function preserves that local link-to-block vector while mapping it to
    world -z. The gripper closing axis remains horizontal and follows yaw.
    """

    link_position = np.asarray(reference_link_position, dtype=np.float64)
    link_rotation = np.asarray(reference_link_rotation, dtype=np.float64)
    block = np.asarray(block_position, dtype=np.float64)
    closing_world = (
        np.array([0.0, 1.0, 0.0], dtype=np.float64)
        if reference_closing_axis_world is None
        else np.asarray(reference_closing_axis_world, dtype=np.float64)
    )
    if link_position.shape != (3,) or block.shape != (3,):
        raise ValueError("link and block positions must each have shape (3,)")
    if link_rotation.shape != (3, 3):
        raise ValueError("link rotation must have shape (3, 3)")

    block_from_link_local = link_rotation.T @ (block - link_position)
    local_forward = block_from_link_local / np.linalg.norm(block_from_link_local)
    local_closing = link_rotation.T @ closing_world
    local_closing -= np.dot(local_closing, local_forward) * local_forward
    local_closing_norm = np.linalg.norm(local_closing)
    if local_closing_norm < 1e-8:
        raise ValueError("reference closing axis cannot be parallel to the block direction")
    local_closing /= local_closing_norm
    local_tangent = np.cross(local_forward, local_closing)

    world_closing = np.array([-np.sin(yaw_rad), np.cos(yaw_rad), 0.0], dtype=np.float64)
    horizontal_forward = np.array([-np.cos(yaw_rad), -np.sin(yaw_rad), 0.0], dtype=np.float64)
    world_forward = (
        np.cos(tilt_rad) * np.array([0.0, 0.0, -1.0], dtype=np.float64)
        + np.sin(tilt_rad) * horizontal_forward
    )
    world_tangent = np.cross(world_forward, world_closing)
    local_basis = np.column_stack((local_closing, local_tangent, local_forward))
    world_basis = np.column_stack((world_closing, world_tangent, world_forward))
    target_rotation = world_basis @ local_basis.T
    blended_rotation = interpolate_rotation_matrix(
        link_rotation, target_rotation, blend_fraction
    )
    blended_link_position = block - blended_rotation @ block_from_link_local
    return blended_link_position, blended_rotation, block_from_link_local
