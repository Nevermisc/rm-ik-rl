#!/usr/bin/env python3
"""Regression checks for v4 same-state/multi-render expert data analysis."""

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


def write_episode(root: Path, index: int, repeat_count: int) -> None:
    directory = root / f"episode_{index:06d}"
    recorder = EpisodeRecorder(
        directory,
        "pick up the red block and place it on the target",
        20.0,
        metadata={
            "task_success": True,
            "transfer_joint_1_rad": 0.8,
            "source_offset_xy_m": [0.01, -0.01],
            "collection_case_id": f"case_{index}",
            "collection_split": "train",
            "collection_simulation_seed": 12345,
            "physical_group_id": "group_a",
            "physical_variant": "exact",
            "render_repeat_index": index,
            "render_repeat_count": repeat_count,
        },
    )
    for frame in range(3):
        image = np.zeros((12, 14, 3), dtype=np.uint8)
        image[..., 0] = 40 + index * 10 + frame
        image[2:8, 3:10, 1] = 180
        recorder.add_frame(
            timestamp_s=frame / 20.0,
            sim_step=frame + 1,
            phase="test",
            joint_position_rad=np.full(6, frame * 0.01, dtype=np.float32),
            gripper_position=frame * 0.1,
            action=np.full(7, frame * 0.02, dtype=np.float32),
            cube_pose_wxyz=np.asarray([0.2, 0.0, 0.7, 1.0, 0.0, 0.0, 0.0]),
            external_rgb=image,
            wrist_rgb=np.roll(image, index + 1, axis=1),
        )
    recorder.save()
    (directory / "task_report.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "unassisted_full_task_complete": True,
                "simulation_only": True,
                "real_robot_command_sent": False,
            }
        ),
        encoding="utf-8",
    )


def run_analyzer(root: Path, plan: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(Path(__file__).with_name("analyze_rm65_v4_render_groups.py")),
            str(root),
            "--plan",
            str(plan),
            "--group",
            "group_a",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "dataset"
        repeat_count = 4
        for index in range(repeat_count):
            write_episode(root, index, repeat_count)
        plan = Path(temporary) / "plan.json"
        plan.write_text(
            json.dumps(
                {
                    "format": "rm65_expert_collection_plan_v1",
                    "cases": [
                        {
                            "case_id": f"case_{index}",
                            "simulation_seed": 12345,
                            "physical_group_id": "group_a",
                            "render_repeat_index": index,
                            "render_repeat_count": repeat_count,
                        }
                        for index in range(repeat_count)
                    ],
                }
            ),
            encoding="utf-8",
        )
        output = Path(temporary) / "analysis.json"
        passed_run = run_analyzer(root, plan, output)
        passed_report = json.loads(output.read_text(encoding="utf-8"))

        changed_path = root / "episode_000003" / "episode.npz"
        with np.load(changed_path) as archive:
            changed = {key: np.asarray(archive[key]) for key in archive.files}
        changed["action"] = changed["action"].copy()
        changed["action"][0, 0] += 0.01
        np.savez_compressed(changed_path, **changed)
        failed_run = run_analyzer(root, plan, output)
        failed_report = json.loads(output.read_text(encoding="utf-8"))

        group = passed_report["groups"][0]
        failed_group = failed_report["groups"][0]
        passed = bool(
            passed_run.returncode == 0
            and passed_report["status"] == "pass"
            and passed_report["episode_count"] == 4
            and passed_report["collection_plan_coverage"]["status"] == "pass"
            and group["simulation_seed_valid"] is True
            and group["command_action_consistency"]["status"] == "pass"
            and group["initial_physical_state_consistency"]["status"] == "pass"
            and group["physical_trajectory_consistency"]["status"] == "pass"
            and group["rtx_image_diversity"]["external"]["status"] == "pass"
            and group["rtx_image_diversity"]["wrist"]["status"] == "pass"
            and failed_run.returncode == 1
            and failed_report["status"] == "fail"
            and failed_group["command_action_consistency"]["status"] == "fail"
        )
        print(f"RM65_V4_RENDER_GROUP_ANALYSIS={'PASS' if passed else 'FAIL'}")
        if not passed:
            print(passed_run.stdout)
            print(passed_run.stderr)
            print(failed_run.stdout)
            print(failed_run.stderr)
        return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
