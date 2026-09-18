#!/usr/bin/env python3
"""Summarize the natural-gravity RM65+4C2 scripted pick-place suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TRIALS = {
    "transfer_0p6_rad": "natural_pick_place_0p6.json",
    "transfer_0p8_rad": "natural_pick_place_0p8.json",
    "transfer_1p0_rad": "natural_pick_place_1p0.json",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    trials = {}
    for name, filename in TRIALS.items():
        path = args.input_dir / filename
        trials[name] = json.loads(path.read_text(encoding="utf-8"))

    passed = [name for name, report in trials.items() if report["status"] == "pass"]
    all_natural = all(report["natural_source_gravity"] for report in trials.values())
    no_policy = all(report["pi05_used"] is False for report in trials.values())
    minimum_lift = min(report["block_lift_height_m"] for report in trials.values())
    maximum_final_error = max(report["final_target_position_error_m"] for report in trials.values())
    maximum_arm_error = max(report["approach_max_arm_joint_error_rad"] for report in trials.values())
    minimum_recent_left_force = min(
        report["close_recent_mean_contact_force_by_body_n"]["tool_l_2"] for report in trials.values()
    )
    minimum_recent_right_force = min(
        report["close_recent_mean_contact_force_by_body_n"]["tool_r_2"] for report in trials.values()
    )
    success = (
        len(passed) == len(trials)
        and all_natural
        and no_policy
        and minimum_lift > 0.03
        and maximum_final_error < 0.05
        and maximum_arm_error < 0.02
        and minimum_recent_left_force > 0.2
        and minimum_recent_right_force > 0.2
    )
    summary = {
        "status": "pass" if success else "fail",
        "simulation_only": True,
        "pi05_used": False,
        "real_robot_command_sent": False,
        "trial_count": len(trials),
        "passed_trials": len(passed),
        "success_rate": len(passed) / len(trials),
        "natural_source_gravity": all_natural,
        "minimum_block_lift_height_m": minimum_lift,
        "maximum_final_target_position_error_m": maximum_final_error,
        "maximum_approach_arm_joint_error_rad": maximum_arm_error,
        "minimum_recent_left_contact_force_n": minimum_recent_left_force,
        "minimum_recent_right_contact_force_n": minimum_recent_right_force,
        "development_assistance": {
            "arm_gravity_disabled_through_transport": True,
            "enlarged_empirical_contact_pads": True,
            "target_platform_collision_enabled_after_transfer": True,
            "release_separation_assist_m": 0.08,
            "release_downward_speed_assist_m_s": 0.10,
        },
        "unassisted_full_task_complete": False,
        "trials": {
            name: {
                "status": report["status"],
                "transfer_joint_1_rad": report["transfer_joint_1_rad"],
                "block_lift_height_m": report["block_lift_height_m"],
                "final_target_position_error_m": report["final_target_position_error_m"],
                "approach_max_arm_joint_error_rad": report["approach_max_arm_joint_error_rad"],
            }
            for name, report in trials.items()
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
