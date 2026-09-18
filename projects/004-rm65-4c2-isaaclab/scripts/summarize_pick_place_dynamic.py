#!/usr/bin/env python3
"""Summarize dynamic-approach RM65 pick/place trials without rerunning Isaac Lab."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--results", type=Path, default=Path("results"))
parser.add_argument("--output", type=Path, default=Path("results/pick_place_dynamic_robustness.json"))
args = parser.parse_args()

distances_cm = (2, 4, 6, 10)
rows = []
for distance_cm in distances_cm:
    path = args.results / f"pick_place_dynamic_{distance_cm}cm.json"
    trial = json.loads(path.read_text(encoding="utf-8"))
    if trial["status"] != "pass":
        raise RuntimeError(f"{path} is not a passing trial")
    if trial["initialized_at_grasp"]:
        raise RuntimeError(f"{path} unexpectedly initialized at grasp")
    if abs(trial["pregrasp_distance_m"] - distance_cm / 100.0) > 1e-9:
        raise RuntimeError(f"{path} has the wrong pregrasp distance")
    if not trial["source_block_temporarily_gravity_disabled"]:
        raise RuntimeError(f"{path} no longer records the source-gravity assistance")
    rows.append(
        {
            "pregrasp_distance_m": trial["pregrasp_distance_m"],
            "block_lift_height_m": trial["block_lift_height_m"],
            "final_target_position_error_m": trial["final_target_position_error_m"],
            "approach_max_arm_joint_error_rad": trial["approach_max_arm_joint_error_rad"],
        }
    )

summary = {
    "status": "pass_with_simulation_assistance",
    "simulation_only": True,
    "pi05_used": False,
    "real_robot_command_sent": False,
    "unassisted_full_task_complete": False,
    "trial_count": len(rows),
    "passed_trials": len(rows),
    "tested_pregrasp_distances_m": [row["pregrasp_distance_m"] for row in rows],
    "minimum_block_lift_height_m": min(row["block_lift_height_m"] for row in rows),
    "maximum_final_target_position_error_m": max(row["final_target_position_error_m"] for row in rows),
    "maximum_approach_arm_joint_error_rad": max(row["approach_max_arm_joint_error_rad"] for row in rows),
    "development_assistance": {
        "source_block_gravity_disabled_until_close": True,
        "target_platform_collision_enabled_after_transfer": True,
        "release_separation_assist_m": 0.05,
        "release_downward_speed_assist_m_s": 0.1,
    },
    "trials": rows,
}

args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2))
