#!/usr/bin/env python3
"""Build a deterministic RM65 scripted-expert collection plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ANGLES = (0.60, 0.70, 0.80, 0.90, 1.00)
OFFSETS = (-0.015, 0.0, 0.015)
PROMPTS = (
    "pick up the block and place it on the target",
    "move the block onto the target platform",
    "grasp the block and put it on the target",
    "lift the block and place it at the target",
    "put the block down on the target platform",
)


def build_plan() -> dict:
    cases = []
    index = 0
    for angle_index, angle in enumerate(ANGLES):
        for x_index, offset_x in enumerate(OFFSETS):
            for y_index, offset_y in enumerate(OFFSETS):
                position_index = x_index * len(OFFSETS) + y_index
                split = "validation" if (angle_index + position_index) % 5 == 0 else "train"
                cases.append(
                    {
                        "case_id": f"case_{index:06d}",
                        "episode_index": index,
                        "split": split,
                        "transfer_joint_1_rad": angle,
                        "source_offset_x_m": offset_x,
                        "source_offset_y_m": offset_y,
                        "prompt": PROMPTS[index % len(PROMPTS)],
                    }
                )
                index += 1
    return {
        "format": "rm65_expert_collection_plan_v1",
        "expert": "scripted",
        "simulation_only": True,
        "pi05_used": False,
        "real_robot_command_sent": False,
        "case_count": len(cases),
        "train_case_count": sum(item["split"] == "train" for item in cases),
        "validation_case_count": sum(item["split"] == "validation" for item in cases),
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_plan()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {key: report[key] for key in ("format", "case_count", "train_case_count", "validation_case_count")},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
