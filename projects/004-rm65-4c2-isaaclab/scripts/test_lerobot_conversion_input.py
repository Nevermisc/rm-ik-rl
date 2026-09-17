#!/usr/bin/env python3
"""Check the image-complete input side of the LeRobot converter."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = Path(__file__).resolve().parent
for path in (PROJECT_ROOT, SCRIPTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from convert_expert_episodes_to_lerobot import discover_episodes
from openpi_extension.expert_episode import EpisodeRecorder


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        recorder = EpisodeRecorder(
            root / "episode_000000",
            "pick up the block",
            20.0,
            metadata={"task_success": True, "collection_split": "train"},
        )
        for index in range(3):
            image = np.full((10, 14, 3), index * 40, dtype=np.uint8)
            recorder.add_frame(
                timestamp_s=index / 20.0,
                sim_step=index * 12,
                phase="test",
                joint_position_rad=np.full(6, index * 0.01),
                gripper_position=index / 2.0,
                action=np.concatenate([np.full(6, index * 0.02), [index / 2.0]]),
                cube_pose_wxyz=np.array([0.2, 0.0, 0.7, 1.0, 0.0, 0.0, 0.0]),
                external_rgb=image,
                wrist_rgb=image,
            )
        recorder.save()
        episodes = discover_episodes(root, collection_split="train")
        no_validation = False
        try:
            discover_episodes(root, collection_split="validation")
        except ValueError:
            no_validation = True
        passed = (
            len(episodes) == 1
            and episodes[0]["states"].shape == (3, 7)
            and episodes[0]["actions"].shape == (3, 7)
            and episodes[0]["fps"] == 20.0
            and episodes[0]["collection_split"] == "train"
            and no_validation
        )
        print(f"LEROBOT_CONVERSION_INPUT={'PASS' if passed else 'FAIL'}")
        return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
