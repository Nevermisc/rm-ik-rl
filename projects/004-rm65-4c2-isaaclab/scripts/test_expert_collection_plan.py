#!/usr/bin/env python3
"""Check collection-plan balance and resumable episode detection."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = Path(__file__).resolve().parent
for path in (PROJECT_ROOT, SCRIPTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_expert_collection_plan import ANGLES, OFFSETS, PROMPTS, build_plan
from openpi_extension.expert_episode import EpisodeRecorder
from run_expert_collection_plan import completed_episode


def main() -> int:
    plan = build_plan()
    committed = json.loads(
        (PROJECT_ROOT / "config/rm65_expert_collection_plan_v1.json").read_text(
            encoding="utf-8"
        )
    )
    cases = plan["cases"]
    combinations = {
        (
            item["transfer_joint_1_rad"],
            item["source_offset_x_m"],
            item["source_offset_y_m"],
        )
        for item in cases
    }
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary) / "episode_000000"
        recorder = EpisodeRecorder(
            directory,
            "pick up the block",
            20.0,
            metadata={"task_success": True, "collection_case_id": "case_000000"},
        )
        for index in range(2):
            image = np.full((8, 8, 3), 40 * index, dtype=np.uint8)
            recorder.add_frame(
                timestamp_s=index / 20.0,
                sim_step=index * 12,
                phase="test",
                joint_position_rad=np.zeros(6),
                gripper_position=0.0,
                action=np.zeros(7),
                cube_pose_wxyz=np.array([0, 0, 0, 1, 0, 0, 0]),
                external_rgb=image,
                wrist_rgb=image,
            )
        recorder.save()
        (directory / "task_report.json").write_text(
            json.dumps({"status": "pass", "unassisted_full_task_complete": True}),
            encoding="utf-8",
        )
        resume_detected = completed_episode(directory, "case_000000")
        wrong_case_rejected = not completed_episode(directory, "case_000001")

    checks = {
        "committed_plan_is_reproducible": committed == plan,
        "case_count": len(cases) == len(ANGLES) * len(OFFSETS) ** 2 == 45,
        "all_conditions_unique": len(combinations) == len(cases),
        "split_counts": plan["train_case_count"] == 36
        and plan["validation_case_count"] == 9,
        "five_prompt_variants": {item["prompt"] for item in cases} == set(PROMPTS),
        "unique_case_ids": len({item["case_id"] for item in cases}) == len(cases),
        "resume_detected": resume_detected,
        "wrong_case_rejected": wrong_case_rejected,
    }
    passed = all(checks.values())
    print(json.dumps({"status": "pass" if passed else "fail", "checks": checks}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
