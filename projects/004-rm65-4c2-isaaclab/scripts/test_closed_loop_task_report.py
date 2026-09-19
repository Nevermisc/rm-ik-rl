#!/usr/bin/env python3
"""Test independent closed-loop report validation."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openpi_extension.closed_loop_report import validate_closed_loop_task_report


def main() -> int:
    checkpoint_id = "rm65_scripted_v1_lora_30k/29999"
    report = {
        "status": "pass",
        "simulation_only": True,
        "pi05_used": True,
        "real_robot_command_sent": False,
        "policy_checkpoint_id": checkpoint_id,
        "action_chunks": 12,
        "executed_actions": 120,
        "source_to_target_xy_distance_m": 0.2,
        "block_lift_height_m": 0.04,
        "final_target_xy_error_m": 0.01,
        "final_target_position_error_m": 0.02,
        "post_release_drift_m": 0.001,
        "final_gripper_normalized": 0.0,
        "all_states_finite": True,
        "episode": {"validation": {"status": "pass"}, "evaluation_only": True},
    }
    assert validate_closed_loop_task_report(
        report, expected_checkpoint_id=checkpoint_id
    )["status"] == "pass"
    wrong_checkpoint = dict(report, policy_checkpoint_id="other/1")
    assert validate_closed_loop_task_report(
        wrong_checkpoint, expected_checkpoint_id=checkpoint_id
    )["status"] == "blocked"
    false_status = dict(report, status="fail")
    assert validate_closed_loop_task_report(
        false_status, expected_checkpoint_id=checkpoint_id
    )["status"] == "blocked"
    incomplete = dict(report)
    incomplete.pop("executed_actions")
    assert validate_closed_loop_task_report(
        incomplete, expected_checkpoint_id=checkpoint_id
    )["status"] == "blocked"
    print(
        json.dumps(
            {
                "status": "pass",
                "wrong_checkpoint_blocked": True,
                "failed_task_blocked": True,
                "missing_execution_evidence_blocked": True,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
