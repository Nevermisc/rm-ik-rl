#!/usr/bin/env python3
"""Verify resume never mixes checkpoints, gripper thresholds, or policy seeds."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from run_pi05_rm65_closed_loop_suite import load_existing_report, validate_evaluation_cases


def write_report(
    path: Path,
    threshold: float | None,
    seed: int | None,
    *,
    historical_threshold: bool = False,
) -> None:
    report = {
        "policy_checkpoint_id": "experiment/29999",
        "pi05_used": True,
        "simulation_only": True,
    }
    if historical_threshold:
        report["criteria"] = {"final_gripper_normalized_lt": threshold}
    elif threshold is not None:
        report["controller_config"] = {"policy_gripper_open_threshold": threshold}
    if seed is not None:
        report["policy_noise_seed"] = seed
        report["deterministic_sampling"] = {"case_seed": seed}
    path.write_text(json.dumps(report), encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "task_report.json"
        write_report(path, 0.20, 8000)
        assert load_existing_report(path, "experiment/29999", 0.20, 8000) is not None
        assert load_existing_report(path, "experiment/29999", 0.12, 8000) is None
        assert load_existing_report(path, "experiment/29999", 0.20, 8001) is None

        write_report(path, 0.12, 9000, historical_threshold=True)
        assert load_existing_report(path, "experiment/29999", 0.12, 9000) is not None
        assert load_existing_report(path, "experiment/29999", 0.20, 9000) is None

        write_report(path, None, 9000)
        assert load_existing_report(path, "experiment/29999", 0.12, 9000) is None

        write_report(path, 0.12, None)
        assert load_existing_report(path, "experiment/29999", 0.12, 9000) is None

    plan_path = (
        Path(__file__).resolve().parents[1]
        / "config"
        / "rm65_pi05_evaluation_plan_deterministic_v1.json"
    )
    cases = json.loads(plan_path.read_text(encoding="utf-8"))["cases"]
    validate_evaluation_cases(cases)
    assert len(cases) == 20
    assert len({case["policy_noise_seed"] for case in cases}) == 20
    try:
        validate_evaluation_cases([dict(cases[0]), dict(cases[0])])
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate evaluation cases must fail closed")

    print(json.dumps({"status": "pass", "checks": 10}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
