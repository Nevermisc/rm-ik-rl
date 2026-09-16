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
    contact_pads_urdf = load_json(result_dir / "contact_pads_urdf_report.json")
    contact_pads_import = load_json(result_dir / "contact_pads_import_report.json")
    contact_pads_inventory = load_json(result_dir / "contact_pads_usd_inventory.json")
    contact_pads_smoke = load_json(result_dir / "contact_pads_articulation_smoke.json")
    contact_pads_ik = load_json(result_dir / "contact_pads_combined_ik.json")
    contact_pads_reach = load_json(result_dir / "contact_pads_reach_robustness.json")
    contact_pads_robustness = load_json(result_dir / "gripper_contact_pad_robustness.json")
    gripper_transport = load_json(result_dir / "gripper_transport_robustness.json")
    observation = load_json(result_dir / "observation.json")
    wrist_follow = load_json(result_dir / "wrist_camera_follow_test.json")
    pi_first = load_json(result_dir / "pi05_interface_final_first.json")
    pi_steady = load_json(result_dir / "pi05_interface_final_steady.json")
    transform = load_json(result_dir / "rm65_policy_transform_test.json")
    guard = load_json(result_dir / "action_guard_test.json")
    assisted_pick_place = load_json(result_dir / "pick_place_assisted_robustness.json")
    dynamic_pick_place = load_json(result_dir / "pick_place_dynamic_robustness.json")
    natural_pick_place = load_json(result_dir / "pick_place_natural_bridge.json")
    natural_wide_contact = load_json(result_dir / "natural_wide_pads_close_065.json")
    natural_single_pass = load_json(result_dir / "natural_pick_place_single_pass.json")
    natural_robustness = load_json(result_dir / "natural_pick_place_robustness.json")
    natural_unassisted_release = load_json(result_dir / "natural_unassisted_release_failure.json")
    natural_place_descent = load_json(result_dir / "natural_place_descent_robustness.json")
    top_down_full_gravity = load_json(result_dir / "top_down_full_gravity_robustness.json")

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
    require(len(contact_pads_urdf["gripper_contact_pads"]) == 2, "two contact pads must be generated")
    require(contact_pads_import["status"] == "pass", "contact-pad USD import failed")
    require(contact_pads_inventory["enabled_collision_prim_count"] == 18, "contact-pad collision count changed")
    require(
        len([item for item in contact_pads_inventory["collisions"] if "contact_pad_box" in item["path"]]) == 2,
        "imported contact pads are missing",
    )
    require(contact_pads_smoke["status"] == "pass", "contact-pad articulation smoke test failed")
    require(contact_pads_ik["status"] == "pass", "contact-pad IK mapping failed")
    require(contact_pads_ik["combined_usd_position_error_m"] < 1e-3, "contact-pad IK error is too large")
    require(contact_pads_reach["status"] == "pass", "contact-pad reach robustness failed")
    require(contact_pads_reach["passed_trials"] == 12, "contact-pad reach regression changed")
    require(contact_pads_robustness["status"] == "pass", "contact-pad static grasp robustness failed")
    require(contact_pads_robustness["passed_trials"] == 5, "contact-pad perturbation count changed")
    require(contact_pads_robustness["maximum_block_displacement_m"] < 0.002, "contact-pad block motion is too large")
    require(gripper_transport["status"] == "pass", "gravity-enabled gripper transport failed")
    require(gripper_transport["passed_trials"] == 3, "gripper transport perturbation count changed")
    require(gripper_transport["gravity_enabled_during_transport"] is True, "transport block gravity was not enabled")
    require(gripper_transport["minimum_block_lift_m"] > 0.02, "transport block lift is too small")
    require(
        gripper_transport["maximum_block_to_tool_relative_position_change_m"] < 0.04,
        "transport block drift is too large",
    )
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
    require(
        assisted_pick_place["status"] == "pass_with_simulation_assistance",
        "assisted pick-place state machine did not pass",
    )
    require(assisted_pick_place["passed_trials"] == 3, "assisted pick-place trial count changed")
    require(assisted_pick_place["pi05_used"] is False, "assisted baseline must not claim pi0.5 control")
    require(
        assisted_pick_place["unassisted_full_task_complete"] is False,
        "assisted baseline must not claim an unassisted full task",
    )
    require(dynamic_pick_place["passed_trials"] == 4, "dynamic approach trial count changed")
    require(dynamic_pick_place["pi05_used"] is False, "dynamic baseline must not claim pi0.5 control")
    require(
        dynamic_pick_place["unassisted_full_task_complete"] is False,
        "dynamic baseline must preserve its simulation assistance",
    )
    require(
        natural_pick_place["status"] == "bilateral_contact_pass_lift_fail",
        "natural-gravity contact/lift boundary changed",
    )
    require(natural_pick_place["natural_source_gravity"] is True, "natural-gravity evidence lost gravity")
    require(natural_wide_contact["natural_source_gravity"] is True, "wide-pad contact lost natural gravity")
    require(
        natural_wide_contact["close_recent_mean_contact_force_by_body_n"]["tool_l_2"] > 0.03
        and natural_wide_contact["close_recent_mean_contact_force_by_body_n"]["tool_r_2"] > 0.03,
        "wide pads did not preserve sustained bilateral contact",
    )
    require(natural_single_pass["status"] == "pass", "natural-gravity 0.8 rad reference no longer passes")
    require(natural_single_pass["natural_source_gravity"] is True, "reference grasp lost natural gravity")
    require(natural_single_pass["block_lift_height_m"] > 0.03, "natural-gravity reference lift is too small")
    require(natural_single_pass["pi05_used"] is False, "scripted reference must not claim pi0.5 control")
    require(natural_robustness["status"] == "fail", "natural robustness result must preserve partial failure")
    require(natural_robustness["passed_trials"] == 1, "natural robustness pass count changed")
    require(natural_unassisted_release["status"] == "fail", "unassisted release failure was not preserved")
    require(natural_unassisted_release["release_unassisted"] is True, "release diagnostic used assistance")
    require(
        natural_place_descent["status"] == "pass_with_simulation_assistance",
        "natural place-descent suite did not pass",
    )
    require(natural_place_descent["passed_trials"] == 3, "place-descent pass count changed")
    require(natural_place_descent["unassisted_release"] is True, "place descent lost natural release")
    require(natural_place_descent["pi05_used"] is False, "place descent must not claim pi0.5 control")
    require(
        top_down_full_gravity["status"] == "pass_in_simulation",
        "top-down full-gravity suite did not pass",
    )
    require(top_down_full_gravity["passed_trials"] == 3, "top-down trial count changed")
    require(
        top_down_full_gravity["unassisted_full_task_complete"] is True,
        "top-down suite lost its unassisted full-task result",
    )
    require(top_down_full_gravity["pi05_used"] is False, "scripted expert must not claim pi0.5")

    summary = {
        "status": "pass_with_known_limitations",
        "stage": "RM65-B + 4C2 asset, full-gravity scripted expert, observation, and pi0.5 interface baseline",
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
            "gripper_contact_pad_static_grasp": {
                "status": "pass",
                "collision_prims": contact_pads_inventory["enabled_collision_prim_count"],
                "perturbation_trials": contact_pads_robustness["trial_count"],
                "passed_trials": contact_pads_robustness["passed_trials"],
                "success_rate": contact_pads_robustness["success_rate"],
                "minimum_left_contact_force_n": contact_pads_robustness[
                    "minimum_left_finger_contact_force_n"
                ],
                "minimum_right_contact_force_n": contact_pads_robustness[
                    "minimum_right_finger_contact_force_n"
                ],
                "maximum_base_contact_force_n": contact_pads_robustness["maximum_base_contact_force_n"],
                "maximum_block_displacement_m": contact_pads_robustness["maximum_block_displacement_m"],
                "arm_reach_regression": {
                    "passed_trials": contact_pads_reach["passed_trials"],
                    "trial_count": contact_pads_reach["trial_count"],
                },
            },
            "gripper_contact_pad_transport": {
                "status": "pass",
                "gravity_enabled_during_transport": True,
                "perturbation_trials": gripper_transport["trial_count"],
                "passed_trials": gripper_transport["passed_trials"],
                "success_rate": gripper_transport["success_rate"],
                "minimum_tool_lift_m": gripper_transport["minimum_tool_lift_m"],
                "minimum_block_lift_m": gripper_transport["minimum_block_lift_m"],
                "maximum_block_to_tool_relative_position_change_m": gripper_transport[
                    "maximum_block_to_tool_relative_position_change_m"
                ],
            },
            "assisted_pick_place_state_machine": {
                "status": "pass_with_simulation_assistance",
                "trials": assisted_pick_place["trial_count"],
                "passed_trials": assisted_pick_place["passed_trials"],
                "transfer_joint_1_rad": assisted_pick_place["transfer_joint_1_rad"],
                "minimum_block_lift_m": assisted_pick_place["minimum_block_lift_m"],
                "minimum_transfer_distance_m": assisted_pick_place["minimum_transfer_distance_m"],
                "maximum_final_target_error_m": assisted_pick_place[
                    "maximum_final_target_error_m"
                ],
                "maximum_post_release_drift_m": assisted_pick_place[
                    "maximum_post_release_drift_m"
                ],
                "pi05_used": False,
                "unassisted_full_task_complete": False,
                "development_assistance": assisted_pick_place["development_assistance"],
            },
            "dynamic_approach_pick_place": {
                "status": dynamic_pick_place["status"],
                "trials": dynamic_pick_place["trial_count"],
                "passed_trials": dynamic_pick_place["passed_trials"],
                "tested_pregrasp_distances_m": dynamic_pick_place["tested_pregrasp_distances_m"],
                "minimum_block_lift_m": dynamic_pick_place["minimum_block_lift_height_m"],
                "maximum_final_target_error_m": dynamic_pick_place[
                    "maximum_final_target_position_error_m"
                ],
                "pi05_used": False,
                "unassisted_full_task_complete": False,
            },
            "natural_gravity_contact_bridge_historical": natural_pick_place,
            "natural_gravity_scripted_pick_place": {
                "status": "historical_partial_with_simulation_assistance",
                "reference_transfer_joint_1_rad": natural_single_pass["transfer_joint_1_rad"],
                "reference_block_lift_m": natural_single_pass["block_lift_height_m"],
                "reference_final_target_error_m": natural_single_pass["final_target_position_error_m"],
                "robustness_trials": natural_robustness["trial_count"],
                "robustness_passed_trials": natural_robustness["passed_trials"],
                "minimum_block_lift_m": natural_robustness["minimum_block_lift_height_m"],
                "maximum_final_target_error_m": natural_robustness[
                    "maximum_final_target_position_error_m"
                ],
                "unassisted_release_status": "fail",
                "pi05_used": False,
                "real_robot_command_sent": False,
                "development_assistance": natural_robustness["development_assistance"],
            },
            "natural_gravity_place_descent": natural_place_descent,
            "top_down_full_gravity_scripted_expert": top_down_full_gravity,
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
            "Historical generic articulation tests found unstable 4C2 moving-link gravity, while the task-specific high-gain software-coupled controller now completes the top-down task with all moving-link gravity enabled; physical mass, inertia, and transmission parameters still need calibration.",
            "The wrist camera is updated from the tool-frame pose in software; its physical mounting transform still needs calibration.",
            "Empirically derived 4C2 contact pads provide sustained bilateral contact and natural-gravity transport, but they still require calibration against the physical gripper.",
            "Dynamic Cartesian approach passes from 2, 4, 6, and 10 cm, but the block gravity remains disabled until gripper closure and release still uses a 50 mm separation assist.",
            "High-level release without a place descent is a historical 1/3 result; a 100 mm Cartesian descent followed by release passes three transfer angles without block pose or velocity injection.",
            "The natural-gravity place baseline disables arm gravity through transport, isolates gravity on six moving finger bodies, uses empirical wide pads and a rotated narrow support, and enables target collision only after descent.",
            "The new top-down grasp keeps link_6 above the support plane, but assumes a 0.65 m robot mounting height that must be measured on the physical setup.",
            "The tested pi0.5 DROID checkpoint produces Franka actions and is never executed on RM65.",
            "The top-down scripted expert is collision-active and gravity-consistent but still uses empirical wide contact pads and reaches about 0.105 rad place tracking error.",
            "An RM65 dataset, fine-tuned checkpoint, and pi0.5 closed-loop evaluation are still required.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
