#!/usr/bin/env python3
"""Unit-check case transitions and grouped rates in RM65 evaluation comparison."""

from __future__ import annotations

import json

from compare_rm65_closed_loop_runs import compare


def summary(statuses: list[str], checkpoint: str) -> dict:
    success_count = sum(status == "pass" for status in statuses)
    return {
        "evaluation_kind": "isaaclab_pi0.5_closed_loop",
        "simulation_only": True,
        "real_robot_command_sent": False,
        "checkpoint": checkpoint,
        "episode_count": len(statuses),
        "success_count": success_count,
        "success_rate": success_count / len(statuses),
        "gate": {"minimum_episode_count": 4, "minimum_success_rate": 0.75},
        "cases": [
            {"case_id": f"eval_{index:03d}", "report": {"status": status}}
            for index, status in enumerate(statuses)
        ],
    }


def main() -> int:
    plan = {
        "cases": [
            {
                "case_id": f"eval_{index:03d}",
                "prompt": "prompt a" if index < 2 else "prompt b",
                "transfer_joint_1_rad": 0.65 if index % 2 == 0 else 0.75,
                "source_offset_x_m": 0.0,
                "source_offset_y_m": 0.0,
            }
            for index in range(4)
        ]
    }
    report = compare(
        summary(["fail", "pass", "pass", "fail"], "v1/29999"),
        summary(["pass", "fail", "pass", "pass"], "v2/29999"),
        plan,
    )
    assert report["transitions"] == {
        "improved": 2,
        "regressed": 1,
        "stable_pass": 1,
        "stable_fail": 0,
        "missing_in_baseline": 0,
        "missing_in_candidate": 0,
    }
    assert report["overall_from_case_reports"]["success_rate_delta"] == 0.25
    assert report["by_prompt"]["prompt a"]["success_rate_delta"] == 0.0
    assert report["by_prompt"]["prompt b"]["success_rate_delta"] == 0.5
    assert report["candidate_gate"]["passed"] is True
    assert report["real_robot_command_sent"] is False
    print(json.dumps({"status": "pass", "checks": 5}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
