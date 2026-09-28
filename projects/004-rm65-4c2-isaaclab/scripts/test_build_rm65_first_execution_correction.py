#!/usr/bin/env python3
"""Unit test for corrected first-policy-execution evidence."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_rm65_first_execution_correction import build_evidence


def task_report(status: str, seed: int, sim_seed: int, chunks: int) -> dict:
    return {
        "status": status,
        "simulation_only": True,
        "real_robot_command_sent": False,
        "pi05_used": True,
        "policy_checkpoint_id": "checkpoint/1",
        "policy_noise_seed": seed,
        "simulation_seed": sim_seed,
        "action_chunks": chunks,
        "executed_actions": chunks * 5,
        "deterministic_sampling": {"chunks": []},
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        plan = {
            "cases": [
                {
                    "case_id": f"case_{index:02d}",
                    "panel": "panel",
                    "policy_noise_seed": index,
                    "simulation_seed": 100 + index,
                    "transfer_joint_1_rad": 0.65,
                    "prompt": "prompt",
                }
                for index in range(20)
            ]
        }
        summary_cases = []
        for case in plan["cases"]:
            report = task_report(
                "fail" if case["case_id"] == "case_00" else "pass",
                case["policy_noise_seed"],
                case["simulation_seed"],
                1,
            )
            if case["case_id"] == "case_00":
                report["action_chunks"] = 0
                report["executed_actions"] = 0
                report["preflight_failure"] = {"kind": "false_rejection"}
            summary_cases.append({"case_id": case["case_id"], "report": report})
        base = {
            "plan": "plan.json",
            "checkpoint": "/checkpoint/1",
            "policy_checkpoint_id": "checkpoint/1",
            "repo_id": "repo",
            "cases": summary_cases,
        }
        base_path = root / "base.json"
        base_path.write_text(json.dumps(base), encoding="utf-8")
        replacement_root = root / "replacements"
        replacement_path = replacement_root / "case_00" / "task_report.json"
        replacement_path.parent.mkdir(parents=True)
        replacement_path.write_text(
            json.dumps(task_report("pass", 0, 100, 2)), encoding="utf-8"
        )

        evidence = build_evidence(
            plan, base, base_path, replacement_root, ["case_00"]
        )
        assert evidence["status"] == "pass"
        assert evidence["success_count"] == 20
        assert evidence["episode_count"] == 20
        assert evidence["gate"]["passed"]
        assert evidence["replacements"][0]["previous_preflight_failure"]
        assert evidence["replacements"][0]["first_policy_execution_status"] == "pass"
        assert evidence["cases"][0]["action_chunks"] == 2

    print(json.dumps({"status": "pass", "checks": 7}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
