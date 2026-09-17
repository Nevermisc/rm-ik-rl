#!/usr/bin/env python3
"""Unit-check the multi-episode task and image-health summary."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openpi_extension.expert_episode import EpisodeRecorder


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        episode_dir = root / "episode_000000"
        recorder = EpisodeRecorder(
            episode_dir,
            "pick up the block",
            20.0,
            metadata={
                "task_success": True,
                "transfer_joint_1_rad": 0.8,
                "source_offset_xy_m": [0.0, 0.0],
            },
        )
        for index in range(4):
            image = np.zeros((30, 30, 3), dtype=np.uint8)
            image[5 + index : 15 + index, 8:18, 0] = 200 + index
            recorder.add_frame(
                timestamp_s=index / 20.0,
                sim_step=index * 12,
                phase="test",
                joint_position_rad=np.full(6, index * 0.01),
                gripper_position=0.0,
                action=np.zeros(7),
                cube_pose_wxyz=np.array([0.2, 0.0, 0.7, 1.0, 0.0, 0.0, 0.0]),
                external_rgb=image,
                wrist_rgb=np.roll(image, index, axis=1),
            )
        recorder.save()
        (episode_dir / "task_report.json").write_text(
            json.dumps(
                {
                    "status": "pass",
                    "unassisted_full_task_complete": True,
                    "pi05_used": False,
                }
            ),
            encoding="utf-8",
        )
        output = root / "summary.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).with_name("summarize_expert_dataset.py")),
                str(root),
                "--output",
                str(output),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        report = json.loads(output.read_text(encoding="utf-8"))
        passed = (
            completed.returncode == 0
            and report["status"] == "pass"
            and report["episode_count"] == 1
            and report["passed_episode_count"] == 1
            and report["episodes"][0]["external_image_metrics"]["passed"] is True
            and report["episodes"][0]["wrist_image_metrics"]["passed"] is True
        )
        print(f"EXPERT_DATASET_SUMMARY={'PASS' if passed else 'FAIL'}")
        if not passed:
            print(completed.stdout)
            print(completed.stderr)
        return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
