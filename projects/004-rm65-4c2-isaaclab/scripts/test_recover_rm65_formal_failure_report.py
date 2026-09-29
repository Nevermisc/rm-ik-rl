#!/usr/bin/env python3
"""Unit tests for fail-closed RM65 formal failure recovery."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from recover_rm65_formal_failure_report import extract_report, recover_report


def main() -> int:
    case = {
        "case_id": "confirm_v3_000",
        "policy_noise_seed": 101,
        "simulation_seed": 201,
        "prompt": "move the block",
        "transfer_joint_1_rad": 0.6625,
        "source_offset_x_m": -0.009,
        "source_offset_y_m": -0.002,
    }
    plan = {
        "frozen_controller_contract": {"checkpoint_id": "checkpoint/9999"},
        "cases": [case],
    }
    original = {
        "status": "fail",
        "simulation_only": True,
        "real_robot_command_sent": False,
        "pi05_used": True,
        "policy_checkpoint_id": "checkpoint/9999",
        "policy_noise_seed": 101,
        "simulation_seed": 201,
        "prompt": "move the block",
        "action_chunks": 10,
    }
    raw = json.dumps(original, indent=2)
    log = f"startup\n{raw}\nRM65_PI05_CLOSED_LOOP=FAIL\nvalidation output\n"
    extracted, extracted_raw = extract_report(log)
    assert extracted == original
    assert json.loads(extracted_raw) == original

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        runner_log = root / "runner.log"
        runner_log.write_text(log, encoding="utf-8")
        recovered = recover_report(
            runner_log,
            plan,
            "confirm_v3_000",
            root / "excluded_retry",
        )
        assert recovered["status"] == "fail"
        assert recovered["transfer_joint_1_rad"] == 0.6625
        assert recovered["source_offset_xy_m"] == [-0.009, -0.002]
        assert recovered["formal_outcome_recovery"]["outcome_changed"] is False
        assert recovered["formal_outcome_recovery"]["invalid_retry_result_excluded"] is True
        tampered = dict(plan)
        tampered["cases"] = [dict(case, policy_noise_seed=999)]
        try:
            recover_report(runner_log, tampered, "confirm_v3_000", root / "excluded_retry")
        except ValueError:
            pass
        else:
            raise AssertionError("seed-mismatched recovery must fail closed")

    print(json.dumps({"status": "pass", "checks": 9}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
