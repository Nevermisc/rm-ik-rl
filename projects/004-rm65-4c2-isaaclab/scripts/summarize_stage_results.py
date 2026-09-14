#!/usr/bin/env python3
"""Validate evidence files and build one machine-readable stage summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--output", type=Path, default=Path("results/stage_summary.json"))
    args = parser.parse_args()

    result_dir = args.results.resolve()
    combined = load_json(result_dir / "combined_urdf_report.json")
    imported = load_json(result_dir / "import_report.json")
    no_gravity = load_json(result_dir / "articulation_smoke_no_gravity.json")
    arm_gravity = load_json(result_dir / "articulation_smoke_arm_gravity.json")
    raw_gravity = load_json(result_dir / "articulation_smoke_gravity.json")
    combined_ik = load_json(result_dir / "combined_ik_test.json")
    observation = load_json(result_dir / "observation.json")
    pi_first = load_json(result_dir / "pi05_interface_final_first.json")
    pi_steady = load_json(result_dir / "pi05_interface_final_steady.json")
    transform = load_json(result_dir / "rm65_policy_transform_test.json")
    guard = load_json(result_dir / "action_guard_test.json")

    require(combined["link_count"] == 16, "combined URDF must contain 16 links")
    require(combined["joint_count"] == 15, "combined URDF must contain 15 joints")
    require(combined["movable_joint_count"] == 12, "combined URDF must contain 12 movable joints")
    require(imported["status"] == "pass", "USD import did not pass")
    require(imported["usd_joint_count"] == 16, "USD joint count changed")
    require(no_gravity["status"] == "pass", "no-gravity articulation check did not pass")
    require(arm_gravity["status"] == "pass", "arm-gravity articulation check did not pass")
    require(arm_gravity["gravity_enabled"] is True, "RM65 gravity was not enabled")
    require(arm_gravity["gripper_gravity_disabled"] is True, "4C2 gravity workaround is missing")
    require(raw_gravity["status"] == "fail", "full-gravity diagnostic must remain a known failure")
    require(combined_ik["status"] == "pass", "combined USD IK mapping did not pass")
    require(combined_ik["lula_joint_names"] == [f"joint_{index}" for index in range(1, 7)], "IK joint order changed")
    require(combined_ik["combined_usd_position_error_m"] < 1e-3, "combined USD position error is too large")
    require(combined_ik["combined_usd_rotation_error_rad"] < 1e-2, "combined USD rotation error is too large")
    require(observation["status"] == "pass", "observation capture did not pass")
    require(observation["images"]["external"]["red_target_pixel_count"] > 20, "target missing externally")
    require(observation["images"]["wrist"]["red_target_pixel_count"] > 20, "target missing in wrist view")
    require(pi_first["status"] == "pass" and pi_steady["status"] == "pass", "pi0.5 dry-run failed")
    require(pi_first["executed"] is False and pi_steady["executed"] is False, "dry-run executed an action")
    require(pi_first["policy_output"]["shape"] == [15, 8], "unexpected pi0.5 output shape")
    require(transform["status"] == "pass", "RM65 OpenPI transform test did not pass")
    require(transform["action_output_shape"][1] == 7, "RM65 transform action width must be seven")
    require(guard["status"] == "pass" and guard["nan_rejected"] is True, "action guard test did not pass")
    require(guard["maximum_output_step_rad"] <= 0.050001, "action guard exceeded step bound")

    summary = {
        "status": "pass_with_known_limitations",
        "stage": "RM65-B + 4C2 asset, observation, and pi0.5 interface baseline",
        "real_robot_command_sent": False,
        "closed_loop_task_complete": False,
        "checks": {
            "combined_urdf": {
                "status": "pass",
                "links": combined["link_count"],
                "joints": combined["joint_count"],
                "movable_joints": combined["movable_joint_count"],
            },
            "usd_import": {"status": "pass", "usd_joints": imported["usd_joint_count"]},
            "articulation_no_gravity": {"status": "pass"},
            "articulation_arm_gravity": {
                "status": "pass",
                "max_arm_return_error_rad": arm_gravity["max_arm_return_error_rad"],
                "max_gripper_return_error_rad": arm_gravity["max_gripper_return_error_rad"],
            },
            "combined_usd_lula_ik": {
                "status": "pass",
                "position_error_m": combined_ik["combined_usd_position_error_m"],
                "rotation_error_rad": combined_ik["combined_usd_rotation_error_rad"],
            },
            "observation": {
                "status": "pass",
                "external_red_pixels": observation["images"]["external"]["red_target_pixel_count"],
                "wrist_red_pixels": observation["images"]["wrist"]["red_target_pixel_count"],
            },
            "pi05_transport_dry_run": {
                "status": "pass",
                "output_shape": pi_first["policy_output"]["shape"],
                "first_latency_seconds": pi_first["latency_seconds"],
                "steady_latency_seconds": pi_steady["latency_seconds"],
                "executed": False,
            },
            "rm65_policy_transform": {"status": "pass", "output_width": 7},
            "action_guard": {
                "status": "pass",
                "nan_rejected": guard["nan_rejected"],
                "maximum_output_step_rad": guard["maximum_output_step_rad"],
            },
        },
        "known_limitations": [
            "The unmodified 4C2 PhysX model is unstable under gravity; the validated baseline disables gravity only for gripper rigid bodies.",
            "The wrist-like view is derived from link_6 but is not yet parented to a moving wrist in a continuous environment.",
            "The tested pi0.5 DROID checkpoint produces Franka actions and is never executed on RM65.",
            "A task scene, expert controller, RM65 dataset, fine-tuned checkpoint, and closed-loop evaluation are still required.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
