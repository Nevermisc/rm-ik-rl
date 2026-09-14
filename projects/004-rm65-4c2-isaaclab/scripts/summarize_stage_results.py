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
    usd_inventory = load_json(result_dir / "usd_physics_inventory.json")
    no_gravity = load_json(result_dir / "articulation_smoke_no_gravity.json")
    arm_gravity = load_json(result_dir / "articulation_smoke_arm_gravity.json")
    raw_gravity = load_json(result_dir / "articulation_smoke_gravity.json")
    no_ground = load_json(result_dir / "diagnostic_full_gravity_no_ground.json")
    high_frequency = load_json(result_dir / "diagnostic_full_gravity_1khz.json")
    distal_isolation = load_json(result_dir / "diagnostic_distal_gravity_isolation.json")
    physics_proxy = load_json(result_dir / "diagnostic_physics_proxy_full_gravity.json")
    combined_ik = load_json(result_dir / "combined_ik_test.json")
    reach_baseline = load_json(result_dir / "reach_baseline.json")
    reach_robustness = load_json(result_dir / "reach_robustness.json")
    gripper_aperture = load_json(result_dir / "gripper_aperture_test.json")
    gripper_close = load_json(result_dir / "gripper_close_stability.json")
    gripper_base_contact = load_json(result_dir / "diagnostic_gripper_base_contact.json")
    observation = load_json(result_dir / "observation.json")
    wrist_follow = load_json(result_dir / "wrist_camera_follow_test.json")
    pi_first = load_json(result_dir / "pi05_interface_final_first.json")
    pi_steady = load_json(result_dir / "pi05_interface_final_steady.json")
    transform = load_json(result_dir / "rm65_policy_transform_test.json")
    guard = load_json(result_dir / "action_guard_test.json")

    require(combined["link_count"] == 16, "combined URDF must contain 16 links")
    require(combined["joint_count"] == 15, "combined URDF must contain 15 joints")
    require(combined["movable_joint_count"] == 12, "combined URDF must contain 12 movable joints")
    require(imported["status"] == "pass", "USD import did not pass")
    require(imported["usd_joint_count"] == 16, "USD joint count changed")
    require(usd_inventory["status"] == "pass", "USD physics inventory did not pass")
    require(usd_inventory["rigid_body_count"] == 16, "USD rigid body count changed")
    require(usd_inventory["enabled_collision_prim_count"] == 16, "enabled collision count changed")
    require(
        usd_inventory["tool_links_with_enabled_collision_count"] == 9,
        "all nine 4C2 links must keep enabled collision geometry",
    )
    tool_collision_prims = [item for item in usd_inventory["collisions"] if item["tool_link"] is not None]
    require(len(tool_collision_prims) == 9, "expected one collision prim per 4C2 link")
    require(
        all(item["mesh_approximation"] == "convexHull" for item in tool_collision_prims),
        "4C2 collision approximation changed",
    )
    require(no_gravity["status"] == "pass", "no-gravity articulation check did not pass")
    require(arm_gravity["status"] == "pass", "arm-gravity articulation check did not pass")
    require(arm_gravity["gravity_enabled"] is True, "RM65 gravity was not enabled")
    require(arm_gravity["gripper_gravity_disabled"] is False, "full-gripper gravity isolation is too broad")
    require(arm_gravity["moving_gripper_gravity_disabled"] is True, "moving-link gravity workaround is missing")
    require(len(arm_gravity["gravity_disabled_body_paths"]) == 6, "exactly six moving gripper bodies must be isolated")
    require(raw_gravity["status"] == "fail", "full-gravity diagnostic must remain a known failure")
    require(no_ground["status"] == "fail" and no_ground["ground_enabled"] is False, "no-ground diagnosis changed")
    require(high_frequency["status"] == "fail" and high_frequency["physics_dt_seconds"] == 0.001, "1 kHz diagnosis changed")
    require(distal_isolation["status"] == "fail", "distal-only gravity diagnosis changed")
    require(physics_proxy["status"] == "fail", "inertia-regularized proxy diagnosis changed")
    require(combined_ik["status"] == "pass", "combined USD IK mapping did not pass")
    require(combined_ik["lula_joint_names"] == [f"joint_{index}" for index in range(1, 7)], "IK joint order changed")
    require(combined_ik["combined_usd_position_error_m"] < 1e-3, "combined USD position error is too large")
    require(combined_ik["combined_usd_rotation_error_rad"] < 1e-2, "combined USD rotation error is too large")
    require(reach_baseline["status"] == "pass", "deterministic reach baseline did not pass")
    require(reach_baseline["simulation_only"] is True, "reach baseline must remain simulation-only")
    require(reach_robustness["status"] == "pass", "multi-target reach suite did not pass")
    require(reach_robustness["success_rate"] >= 0.95, "multi-target reach success rate is too low")
    require(gripper_aperture["status"] == "pass", "gripper aperture geometry check did not pass")
    require(gripper_aperture["all_pair_distances_monotonic"] is True, "gripper aperture is not monotonic")
    require(gripper_close["status"] == "pass", "gripper close stability check did not pass")
    require(gripper_close["lift_attempted"] is False, "default close check must not attempt unstable lift")
    require(gripper_close["contact_confirmed"] is False, "contact must not be claimed without a sensor")
    require(gripper_close["bilateral_fingertip_contact_confirmed"] is False, "bilateral grasp contact is not validated")
    require(gripper_close["support_surface_present"] is False, "close check must not mix table contact into the result")
    require(gripper_close["contact_block_gravity_disabled"] is True, "floating diagnostic block changed")
    require(gripper_close["contact_processing_disabled"] is False, "global contact processing must be enabled")
    gripper_sensor_bindings = {
        name: binding
        for name, binding in gripper_close["contact_sensor_binding"].items()
        if name.startswith("tool_")
    }
    require(len(gripper_sensor_bindings) == 9, "all nine prefixed 4C2 links must have sensors")
    require(
        all(binding == {"body_count": 1, "filter_count": 1} for binding in gripper_sensor_bindings.values()),
        "each gripper body must have a one-body, one-filter contact view",
    )
    require(
        gripper_close["contact_sensor_binding"]["cube_any_contact"]
        == {"body_count": 1, "filter_count": 0},
        "the contact block must have an unfiltered one-body contact view",
    )
    require(
        gripper_close["contact_sensor_binding"]["tool_base_link"]
        == {"body_count": 1, "filter_count": 1},
        "the gripper base contact view changed",
    )
    require(gripper_close["contact_block_size_m"] == [0.06, 0.04, 0.025], "contact block geometry changed")
    require(gripper_close["contact_block_inward_offset_m"] == -0.01, "safe outward block offset changed")
    require(gripper_close["closed_l2_tip_gap_m"] < gripper_close["contact_block_size_m"][1], "l2 proxy gap did not cross the block width")
    require(gripper_close["closed_l3_tip_gap_m"] < gripper_close["contact_block_size_m"][1], "l3 proxy gap did not cross the block width")
    require(gripper_base_contact["contact_confirmed"] is True, "base-contact diagnostic lost contact")
    require(gripper_base_contact["bilateral_fingertip_contact_confirmed"] is False, "base-contact diagnostic must not claim grasp")
    require(gripper_base_contact["cube_contact_force_by_gripper_body_n"]["tool_base_link"] > 0.1, "base contact force changed")
    require(gripper_base_contact["left_finger_contact_force_n"] == 0.0, "unexpected left-finger contact")
    require(gripper_base_contact["right_finger_contact_force_n"] == 0.0, "unexpected right-finger contact")
    require(observation["status"] == "pass", "observation capture did not pass")
    require(observation["images"]["external"]["red_target_pixel_count"] > 20, "target missing externally")
    require(observation["images"]["wrist"]["red_target_pixel_count"] > 20, "target missing in wrist view")
    require(wrist_follow["status"] == "pass", "wrist camera follow test did not pass")
    require(wrist_follow["camera_follows_tool_pose"] is True, "wrist camera follow mode is disabled")
    require(wrist_follow["camera_follow_check"]["passed"] is True, "wrist camera tool-frame transform changed")
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
            "usd_physics_inventory": {
                "status": "pass",
                "rigid_bodies": usd_inventory["rigid_body_count"],
                "enabled_collision_prims": usd_inventory["enabled_collision_prim_count"],
                "tool_links_with_enabled_collision": usd_inventory["tool_links_with_enabled_collision_count"],
                "tool_collision_approximation": "convexHull",
            },
            "articulation_no_gravity": {"status": "pass"},
            "articulation_arm_gravity": {
                "status": "pass",
                "gravity_isolated_moving_gripper_bodies": 6,
                "max_arm_return_error_rad": arm_gravity["max_arm_return_error_rad"],
                "max_gripper_return_error_rad": arm_gravity["max_gripper_return_error_rad"],
            },
            "combined_usd_lula_ik": {
                "status": "pass",
                "position_error_m": combined_ik["combined_usd_position_error_m"],
                "rotation_error_rad": combined_ik["combined_usd_rotation_error_rad"],
            },
            "deterministic_pregrasp_reach": {
                "status": "pass",
                "initial_position_error_m": reach_baseline["initial_position_error_m"],
                "final_position_error_m": reach_baseline["final_position_error_m"],
                "maximum_command_step_rad": reach_baseline["maximum_command_step_rad"],
            },
            "multi_target_reach_robustness": {
                "status": "pass",
                "trials": reach_robustness["trial_count"],
                "passed_trials": reach_robustness["passed_trials"],
                "success_rate": reach_robustness["success_rate"],
                "worst_position_error_m": reach_robustness["worst_final_position_error_m"],
                "worst_rotation_error_rad": reach_robustness["worst_final_rotation_error_rad"],
                "maximum_command_step_rad": reach_robustness["maximum_command_step_rad"],
            },
            "gripper_aperture_geometry": {
                "status": "pass",
                "zero_rad_semantics": "open",
                "positive_direction_semantics": "closing",
                "l2_pair_total_distance_change_m": gripper_aperture["pair_trends"][
                    "tool_l_2_to_tool_r_2"
                ]["total_change_m"],
                "l3_pair_total_distance_change_m": gripper_aperture["pair_trends"][
                    "tool_l_3_to_tool_r_3"
                ]["total_change_m"],
            },
            "gripper_static_close_stability": {
                "status": "pass",
                "all_states_finite": gripper_close["all_states_finite"],
                "contact_confirmed": False,
                "lift_attempted": False,
                "floating_block_displacement_m": gripper_close["cube_displacement_during_close_m"],
                "contact_processing_enabled": not gripper_close["contact_processing_disabled"],
                "sensor_bindings_valid": True,
            },
            "gripper_base_contact_diagnostic": {
                "status": "known_failure",
                "base_contact_force_n": gripper_base_contact["cube_contact_force_by_gripper_body_n"][
                    "tool_base_link"
                ],
                "block_displacement_m": gripper_base_contact["cube_displacement_during_close_m"],
                "bilateral_fingertip_contact_confirmed": False,
            },
            "observation": {
                "status": "pass",
                "external_red_pixels": observation["images"]["external"]["red_target_pixel_count"],
                "wrist_red_pixels": observation["images"]["wrist"]["red_target_pixel_count"],
            },
            "wrist_camera_follow": {
                "status": "pass",
                "camera_motion_m": wrist_follow["camera_follow_check"]["camera_motion_m"],
                "camera_to_tool_distance_change_m": wrist_follow["camera_follow_check"][
                    "camera_to_tool_distance_change_m"
                ],
                "maximum_pose_command_error_m": max(
                    wrist_follow["camera_follow_check"]["first_pose_command_error_m"],
                    wrist_follow["camera_follow_check"]["second_pose_command_error_m"],
                ),
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
            "The unmodified 4C2 moving links are unstable under PhysX gravity; the validated baseline disables gravity for the six moving finger bodies while retaining gravity on the gripper base and two fixed supports.",
            "The wrist camera is updated from the tool-frame pose in software; its physical mounting transform still needs calibration.",
            "Static gripper closing is finite, but the safe outward block pose has no contact while the zero-offset pose contacts only tool_base_link and ejects the block; bilateral fingertip contact is not validated and the 4C2 collision approximation must be rebuilt.",
            "The tested pi0.5 DROID checkpoint produces Franka actions and is never executed on RM65.",
            "A task scene, expert controller, RM65 dataset, fine-tuned checkpoint, and closed-loop evaluation are still required.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
