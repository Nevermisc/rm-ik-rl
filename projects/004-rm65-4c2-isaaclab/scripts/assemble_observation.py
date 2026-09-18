#!/usr/bin/env python3
"""Combine separately rendered external and wrist reports into one observation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external", type=Path, required=True)
    parser.add_argument("--wrist", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    external = json.loads(args.external.read_text(encoding="utf-8"))
    wrist = json.loads(args.wrist.read_text(encoding="utf-8"))
    if external["status"] != "pass" or wrist["status"] != "pass":
        raise ValueError("both single-view reports must pass")
    for field in ("joint_names", "rm65_joint_position_rad", "gripper_joint_position_rad"):
        if external[field] != wrist[field]:
            raise ValueError(f"view reports disagree on {field}")
    report = {
        "status": "pass",
        "usd": external["usd"],
        "capture_mode": "two isolated Isaac Sim processes",
        "joint_names": external["joint_names"],
        "body_names": external["body_names"],
        "rm65_joint_position_rad": external["rm65_joint_position_rad"],
        "gripper_joint_position_rad": external["gripper_joint_position_rad"],
        "images": {"external": external["image"], "wrist": wrist["image"]},
        "camera_poses": {
            "external": {"eye": external["camera_eye_world_m"], "target": external["camera_target_world_m"]},
            "wrist": {"eye": wrist["camera_eye_world_m"], "target": wrist["camera_target_world_m"]},
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("ASSEMBLE_OBSERVATION=PASS")


if __name__ == "__main__":
    main()
