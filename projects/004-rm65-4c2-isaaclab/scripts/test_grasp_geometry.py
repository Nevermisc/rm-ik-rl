#!/usr/bin/env python3
"""Unit checks for the above-table grasp geometry helper."""

from __future__ import annotations

import json

import numpy as np

from grasp_geometry import compute_top_down_link_pose, interpolate_rotation_matrix


def main() -> int:
    angle = 0.47
    reference_rotation = np.array(
        [
            [np.cos(angle), 0.0, np.sin(angle)],
            [0.0, 1.0, 0.0],
            [-np.sin(angle), 0.0, np.cos(angle)],
        ],
        dtype=np.float64,
    )
    reference_link = np.array([-0.14, 0.0, 0.65], dtype=np.float64)
    block = np.array([-0.22, 0.0, 0.745], dtype=np.float64)
    yaw = 0.8
    tilt = 0.35
    top_link, top_rotation, local_offset = compute_top_down_link_pose(
        reference_link, reference_rotation, block, yaw, tilt, 1.0
    )
    translation = np.array([0.02, -0.015, 0.0], dtype=np.float64)
    translated_link, translated_rotation, translated_local_offset = compute_top_down_link_pose(
        reference_link + translation,
        reference_rotation,
        block + translation,
        yaw,
        tilt,
        1.0,
    )

    mapped_offset = top_rotation @ local_offset
    expected_closing = np.array([-np.sin(yaw), np.cos(yaw), 0.0], dtype=np.float64)
    local_closing = reference_rotation.T @ np.array([0.0, 1.0, 0.0], dtype=np.float64)
    mapped_closing = top_rotation @ local_closing
    expected_forward = np.array(
        [
            -np.sin(tilt) * np.cos(yaw),
            -np.sin(tilt) * np.sin(yaw),
            -np.cos(tilt),
        ],
        dtype=np.float64,
    )
    checks = {
        "rotation_orthonormal": bool(
            np.allclose(top_rotation.T @ top_rotation, np.eye(3), atol=1e-10)
        ),
        "proper_rotation": bool(np.isclose(np.linalg.det(top_rotation), 1.0, atol=1e-10)),
        "block_direction_matches_tilt": bool(
            np.allclose(mapped_offset / np.linalg.norm(mapped_offset), expected_forward, atol=1e-10)
            and mapped_offset[2] < 0.0
        ),
        "closing_axis_matches_yaw": bool(
            np.allclose(mapped_closing, expected_closing, atol=1e-10)
        ),
        "link_is_above_block": bool(top_link[2] > block[2]),
        "calibrated_offset_preserved": bool(
            np.allclose(top_link + mapped_offset, block, atol=1e-10)
        ),
        "source_xy_translation_preserves_grasp": bool(
            np.allclose(translated_link, top_link + translation, atol=1e-10)
            and np.allclose(translated_rotation, top_rotation, atol=1e-10)
            and np.allclose(translated_local_offset, local_offset, atol=1e-10)
        ),
        "blend_zero_is_reference": bool(
            np.allclose(
                interpolate_rotation_matrix(reference_rotation, top_rotation, 0.0),
                reference_rotation,
                atol=1e-10,
            )
        ),
        "blend_one_is_target": bool(
            np.allclose(
                interpolate_rotation_matrix(reference_rotation, top_rotation, 1.0),
                top_rotation,
                atol=1e-10,
            )
        ),
    }
    report = {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "top_down_link_position_m": top_link.tolist(),
        "block_position_m": block.tolist(),
        "block_from_link_world_m": mapped_offset.tolist(),
        "rotation_determinant": float(np.linalg.det(top_rotation)),
    }
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
