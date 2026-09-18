#!/usr/bin/env python3
"""Summarize full-gravity above-table RM65 pick/place trials."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TRIALS = {
    "transfer_0p6_rad": "top_down_full_gravity_0p6.json",
    "transfer_0p8_rad": "top_down_full_gravity_0p8.json",
    "transfer_1p0_rad": "top_down_full_gravity_1p0.json",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    trials = {
        name: json.loads((args.input_dir / filename).read_text(encoding="utf-8"))
        for name, filename in TRIALS.items()
    }
    passed = [name for name, report in trials.items() if report["status"] == "pass"]
    minimum_lift = min(report["block_lift_height_m"] for report in trials.values())
    maximum_final_error = max(
        report["final_target_position_error_m"] for report in trials.values()
    )
    maximum_place_arm_error = max(
        report["place_max_arm_joint_error_rad"] for report in trials.values()
    )
    maximum_release_drift = max(report["post_release_drift_m"] for report in trials.values())
    all_unassisted = all(
        report["unassisted_full_task_complete"]
        and not report["moving_gripper_gravity_disabled"]
        and not report["arm_gravity_disabled_through_transport"]
        for report in trials.values()
    )
    success = (
        len(passed) == len(trials)
        and minimum_lift > 0.03
        and maximum_final_error < 0.05
        and maximum_place_arm_error < 0.15
        and maximum_release_drift < 0.02
        and all_unassisted
    )
    summary = {
        "status": "pass_in_simulation" if success else "fail",
        "simulation_only": True,
        "pi05_used": False,
        "real_robot_command_sent": False,
        "expert": "scripted Cartesian approach and joint-space transfer",
        "trial_count": len(trials),
        "passed_trials": len(passed),
        "success_rate": len(passed) / len(trials),
        "minimum_block_lift_height_m": minimum_lift,
        "maximum_final_target_position_error_m": maximum_final_error,
        "maximum_place_arm_joint_error_rad": maximum_place_arm_error,
        "maximum_post_release_drift_m": maximum_release_drift,
        "unassisted_full_task_complete": all_unassisted,
        "development_assistance": {
            "enlarged_empirical_contact_pads": True,
            "scripted_expert_waypoints": True,
            "robot_base_height_assumed_m": 0.65,
        },
        "trials": {
            name: {
                "status": report["status"],
                "transfer_joint_1_rad": report["transfer_joint_1_rad"],
                "block_lift_height_m": report["block_lift_height_m"],
                "place_max_arm_joint_error_rad": report["place_max_arm_joint_error_rad"],
                "final_target_position_error_m": report["final_target_position_error_m"],
                "post_release_drift_m": report["post_release_drift_m"],
                "unassisted_full_task_complete": report["unassisted_full_task_complete"],
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
