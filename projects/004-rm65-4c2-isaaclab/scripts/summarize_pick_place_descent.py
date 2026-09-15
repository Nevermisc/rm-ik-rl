#!/usr/bin/env python3
"""Summarize natural-gravity pick/place with Cartesian descent and unassisted release."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TRIALS = {
    "transfer_0p6_rad": "natural_place_descent_0p6.json",
    "transfer_0p8_rad": "natural_place_descent_0p8.json",
    "transfer_1p0_rad": "natural_place_descent_1p0.json",
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
    maximum_final_error = max(report["final_target_position_error_m"] for report in trials.values())
    maximum_place_arm_error = max(report["place_max_arm_joint_error_rad"] for report in trials.values())
    all_unassisted_release = all(
        report["release_unassisted"]
        and report["release_separation_assist_m"] == 0.0
        and report["release_downward_speed_assist_m_s"] == 0.0
        for report in trials.values()
    )
    success = (
        len(passed) == len(trials)
        and minimum_lift > 0.03
        and maximum_final_error < 0.05
        and maximum_place_arm_error < 0.02
        and all_unassisted_release
    )
    summary = {
        "status": "pass_with_simulation_assistance" if success else "fail",
        "simulation_only": True,
        "pi05_used": False,
        "real_robot_command_sent": False,
        "trial_count": len(trials),
        "passed_trials": len(passed),
        "success_rate": len(passed) / len(trials),
        "minimum_block_lift_height_m": minimum_lift,
        "maximum_final_target_position_error_m": maximum_final_error,
        "maximum_place_arm_joint_error_rad": maximum_place_arm_error,
        "unassisted_release": all_unassisted_release,
        "unassisted_full_task_complete": False,
        "development_assistance": {
            "arm_gravity_disabled_through_transport": True,
            "moving_finger_gravity_disabled": True,
            "enlarged_empirical_contact_pads": True,
            "rotated_narrow_target_support": True,
            "target_collision_enable_stage": "after_place_descent",
        },
        "trials": {
            name: {
                "status": report["status"],
                "transfer_joint_1_rad": report["transfer_joint_1_rad"],
                "block_lift_height_m": report["block_lift_height_m"],
                "place_actual_link_translation_m": report["place_actual_link_translation_m"],
                "place_max_arm_joint_error_rad": report["place_max_arm_joint_error_rad"],
                "final_target_position_error_m": report["final_target_position_error_m"],
                "post_release_drift_m": report["post_release_drift_m"],
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
