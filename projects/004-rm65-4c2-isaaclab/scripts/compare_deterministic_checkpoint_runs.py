#!/usr/bin/env python3
"""Compare RM65 deterministic probes from separate policy-server processes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.expanduser().resolve().read_text(encoding="utf-8"))


def comparable_records(report: dict) -> list[dict]:
    return [
        {
            "request_index": record.get("request_index"),
            "seed": record.get("seed"),
            "noise_sha256": record.get("noise_sha256"),
            "action_shape": record.get("action_shape"),
            "action_dtype": record.get("action_dtype"),
            "action_sha256": record.get("action_sha256"),
        }
        for record in report.get("records", [])
    ]


def compare(first: dict, second: dict) -> dict:
    checks = {
        "first_probe_passed": first.get("status") == "pass",
        "second_probe_passed": second.get("status") == "pass",
        "no_simulation_action_executed": first.get("simulation_action_executed") is False
        and second.get("simulation_action_executed") is False,
        "no_real_robot_command_sent": first.get("real_robot_command_sent") is False
        and second.get("real_robot_command_sent") is False,
        "checkpoint_matches": first.get("server_metadata", {}).get("checkpoint")
        == second.get("server_metadata", {}).get("checkpoint"),
        "repo_id_matches": first.get("server_metadata", {}).get("repo_id")
        == second.get("server_metadata", {}).get("repo_id"),
        "episode_matches": first.get("episode") == second.get("episode"),
        "frame_index_matches": first.get("frame_index") == second.get("frame_index"),
        "request_schedule_matches": first.get("request_schedule")
        == second.get("request_schedule"),
        "noise_and_actions_bit_exact_after_restart": comparable_records(first)
        == comparable_records(second),
    }
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "status": "pass" if not failed else "fail",
        "validation_kind": "rm65_pi05_deterministic_server_restart_comparison",
        "simulation_action_executed": False,
        "real_robot_command_sent": False,
        "checks": checks,
        "failed_checks": failed,
        "checkpoint": first.get("server_metadata", {}).get("checkpoint"),
        "episode": first.get("episode"),
        "frame_index": first.get("frame_index"),
        "policy_noise_seed": first.get("policy_noise_seed"),
        "records": comparable_records(first),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = compare(load(args.first), load(args.second))
    text = json.dumps(report, indent=2) + "\n"
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
