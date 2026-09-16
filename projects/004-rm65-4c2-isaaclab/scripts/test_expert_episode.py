#!/usr/bin/env python3
"""Unit-check the RM65 intermediate expert episode recorder."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openpi_extension.expert_episode import EpisodeRecorder, normalize_gripper, validate_episode


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        episode_dir = Path(temporary) / "episode_000000"
        recorder = EpisodeRecorder(
            output_dir=episode_dir,
            prompt="pick up the red block and place it on the target",
            control_hz=20.0,
            metadata={"simulation_only": True, "expert": "unit_test"},
        )
        for index in range(4):
            joints = np.arange(6, dtype=np.float32) * 0.1 + index * 0.01
            gripper = normalize_gripper(index * 0.1)
            action = np.concatenate([joints + 0.02, [min(gripper + 0.1, 1.0)]])
            cube_pose = np.array([0.2, 0.0, 0.7, 1.0, 0.0, 0.0, 0.0])
            image = np.full((8, 12, 3), index * 20, dtype=np.uint8)
            recorder.add_frame(
                timestamp_s=index / 20.0,
                sim_step=index * 12,
                phase="approach" if index < 2 else "close",
                joint_position_rad=joints,
                gripper_position=gripper,
                action=action,
                cube_pose_wxyz=cube_pose,
                external_rgb=image,
                wrist_rgb=np.flip(image, axis=1),
            )
        manifest = recorder.save()
        report = validate_episode(episode_dir, require_images=True)
        low_dimensional_dir = Path(temporary) / "episode_000001"
        low_dimensional = EpisodeRecorder(
            output_dir=low_dimensional_dir,
            prompt="pick up the block",
            control_hz=20.0,
        )
        for index in range(2):
            low_dimensional.add_frame(
                timestamp_s=index / 20.0,
                sim_step=index * 12,
                phase="approach",
                joint_position_rad=np.zeros(6),
                gripper_position=0.0,
                action=np.zeros(7),
                cube_pose_wxyz=np.array([0.2, 0.0, 0.7, 1.0, 0.0, 0.0, 0.0]),
            )
        low_dimensional.save()
        low_dimensional_report = validate_episode(low_dimensional_dir)
        with np.load(episode_dir / "episode.npz") as arrays:
            checks = {
                "manifest_frame_count": manifest["frame_count"] == 4,
                "state_shape": arrays["observation_state"].shape == (4, 7),
                "action_shape": arrays["action"].shape == (4, 7),
                "phase_shape": arrays["phase_id"].shape == (4,),
                "validator_passed": report["status"] == "pass",
                "images_recorded": report["images_recorded"] is True,
                "low_dimensional_validator_passed": low_dimensional_report["status"] == "pass",
                "low_dimensional_images_absent": low_dimensional_report["images_recorded"] is False,
            }
        result = {"status": "pass" if all(checks.values()) else "fail", "checks": checks}
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
