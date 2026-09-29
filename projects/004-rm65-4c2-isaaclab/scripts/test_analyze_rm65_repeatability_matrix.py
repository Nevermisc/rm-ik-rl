#!/usr/bin/env python3
"""Unit tests for the RM65 three-run repeatability matrix."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from analyze_rm65_repeatability_matrix import build_analysis


def report(case: dict, status: str, image_suffix: str) -> dict:
    return {
        "status": status,
        "simulation_only": True,
        "real_robot_command_sent": False,
        "pi05_used": True,
        "policy_checkpoint_id": "checkpoint/1",
        "policy_noise_seed": case["policy_noise_seed"],
        "simulation_seed": case["simulation_seed"],
        "prompt": case["prompt"],
        "transfer_joint_1_rad": case["transfer_joint_1_rad"],
        "source_offset_xy_m": [
            case["source_offset_x_m"],
            case["source_offset_y_m"],
        ],
        "action_chunks": 1,
        "executed_actions": 5,
        "initial_policy_observation": {"chunk_index": 0},
        "deterministic_sampling": {
            "chunks": [
                {
                    "noise_sha256": "same-noise",
                    "raw_action_sha256": f"action-{image_suffix}",
                    "observation_sha256": {
                        "joint_position": "same-joint",
                        "gripper_position": "same-gripper",
                        "external_image": f"external-{image_suffix}",
                        "wrist_image": f"wrist-{image_suffix}",
                        "cube_position": "same-cube-position",
                        "cube_quaternion": "same-cube-quaternion",
                        "wrist_tool_position": f"tool-position-{image_suffix}",
                        "wrist_tool_quaternion": "same-tool-quaternion",
                        "wrist_camera_eye": "same-camera-eye",
                        "wrist_camera_forward": "same-camera-forward",
                    },
                }
            ]
        },
        "block_lift_height_m": 0.03,
    }


def main() -> int:
    cases = [
        {
            "case_id": "stable", "policy_noise_seed": 1, "simulation_seed": 11,
            "prompt": "move the block", "transfer_joint_1_rad": 0.8,
            "source_offset_x_m": 0.002, "source_offset_y_m": -0.003,
        },
        {
            "case_id": "flip", "policy_noise_seed": 2, "simulation_seed": 12,
            "prompt": "place the block", "transfer_joint_1_rad": 0.9,
            "source_offset_x_m": -0.004, "source_offset_y_m": 0.006,
        },
    ]
    plan = {
        "cases": cases,
        "preregistration": {"repeat_count": 3},
        "frozen_controller_contract": {"checkpoint_id": "checkpoint/1"},
        "repeatability_gate": {
            "required_reports": 6,
            "minimum_status_consistency_rate": 0.5,
            "maximum_outcome_flip_cases": 1,
        },
    }
    with tempfile.TemporaryDirectory() as temporary_directory:
        base = Path(temporary_directory)
        roots = [base / f"run_{index}" for index in range(3)]
        for run_index, root in enumerate(roots):
            for case in cases:
                case_dir = root / case["case_id"]
                case_dir.mkdir(parents=True)
                status = "fail" if case["case_id"] == "flip" and run_index == 2 else "pass"
                (case_dir / "task_report.json").write_text(
                    json.dumps(report(case, status, str(run_index))), encoding="utf-8"
                )
        analysis = build_analysis(plan, roots)
        assert analysis["status"] == "pass"
        assert analysis["valid_report_count"] == 6
        assert analysis["status_consistent_case_count"] == 1
        assert analysis["status_consistency_rate"] == 0.5
        assert analysis["outcome_flip_case_count"] == 1
        assert analysis["chunk_zero_hash_match_case_counts"]["joint_position"] == 2
        assert analysis["chunk_zero_hash_match_case_counts"]["external_image"] == 0
        assert analysis["chunk_zero_hash_match_case_counts"]["noise"] == 2
        assert analysis["chunk_zero_hash_match_case_counts"]["raw_action"] == 0
        assert (
            analysis["chunk_zero_physical_state_hash_available_case_counts"][
                "cube_position"
            ]
            == 2
        )
        assert (
            analysis["chunk_zero_physical_state_hash_match_case_counts"][
                "cube_position"
            ]
            == 2
        )
        assert (
            analysis["chunk_zero_physical_state_hash_match_case_counts"][
                "wrist_tool_position"
            ]
            == 0
        )

    print(json.dumps({"status": "pass", "checks": 12}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
