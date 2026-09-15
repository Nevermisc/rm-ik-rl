#!/usr/bin/env python3
"""Pure NumPy helpers for deriving RM65 grasp poses."""

from __future__ import annotations

import numpy as np


def compute_top_down_link_pose(
    reference_link_position: np.ndarray,
    reference_link_rotation: np.ndarray,
    block_position: np.ndarray,
    yaw_rad: float,
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

    world_forward = np.array([0.0, 0.0, -1.0], dtype=np.float64)
    world_closing = np.array([-np.sin(yaw_rad), np.cos(yaw_rad), 0.0], dtype=np.float64)
    world_tangent = np.cross(world_forward, world_closing)
    local_basis = np.column_stack((local_closing, local_tangent, local_forward))
    world_basis = np.column_stack((world_closing, world_tangent, world_forward))
    top_down_rotation = world_basis @ local_basis.T
    top_down_link_position = block - top_down_rotation @ block_from_link_local
    return top_down_link_position, top_down_rotation, block_from_link_local
