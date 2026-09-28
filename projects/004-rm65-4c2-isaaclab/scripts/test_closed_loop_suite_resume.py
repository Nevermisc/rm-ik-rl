#!/usr/bin/env python3
"""Verify resume never mixes checkpoints, thresholds, policy seeds, or simulation seeds."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from run_pi05_rm65_closed_loop_suite import (
    evaluate_suite_gate,
    load_existing_report,
    validate_evaluation_cases,
)


def write_report(
    path: Path,
    threshold: float | None,
    actual_threshold: float | None,
    seed: int | None,
    simulation_seed: int | None,
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
        report["controller_config"] = {
            "policy_gripper_open_threshold": threshold,
            "policy_gripper_actual_open_threshold": actual_threshold,
            "policy_max_action_chunks": 120,
        }
    if seed is not None:
        report["policy_noise_seed"] = seed
        report["deterministic_sampling"] = {"case_seed": seed}
    if simulation_seed is not None:
        report["simulation_seed"] = simulation_seed
        report["simulation_determinism"] = {"seed": simulation_seed}
    path.write_text(json.dumps(report), encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "task_report.json"
        write_report(path, 0.12, 0.20, 8000, 7000)
        assert load_existing_report(path, "experiment/29999", 0.12, 0.20, 120, 8000, 7000) is not None
        assert load_existing_report(path, "experiment/29999", 0.10, 0.20, 120, 8000, 7000) is None
        assert load_existing_report(path, "experiment/29999", 0.12, 0.25, 120, 8000, 7000) is None
        assert load_existing_report(path, "experiment/29999", 0.12, 0.20, 80, 8000, 7000) is None
        assert load_existing_report(path, "experiment/29999", 0.12, 0.20, 120, 8001, 7000) is None
        assert load_existing_report(path, "experiment/29999", 0.12, 0.20, 120, 8000, 7001) is None

        write_report(path, 0.12, 0.20, 9000, 7000, historical_threshold=True)
        assert load_existing_report(path, "experiment/29999", 0.12, 0.20, 120, 9000, 7000) is None

        write_report(path, None, None, 9000, 7000)
        assert load_existing_report(path, "experiment/29999", 0.12, 0.20, 120, 9000, 7000) is None

        write_report(path, 0.12, 0.20, None, 7000)
        assert load_existing_report(path, "experiment/29999", 0.12, 0.20, 120, 9000, 7000) is None

        write_report(path, 0.12, 0.20, 9000, None)
        assert load_existing_report(path, "experiment/29999", 0.12, 0.20, 120, 9000, 7000) is None

    plan_path = (
        Path(__file__).resolve().parents[1]
        / "config"
        / "rm65_pi05_evaluation_plan_deterministic_v1.json"
    )
    cases = json.loads(plan_path.read_text(encoding="utf-8"))["cases"]
    validate_evaluation_cases(cases)
    assert len(cases) == 20
    assert len({case["policy_noise_seed"] for case in cases}) == 20
    assert len({case["simulation_seed"] for case in cases}) == 20
    try:
        validate_evaluation_cases([dict(cases[0]), dict(cases[0])])
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate evaluation cases must fail closed")

    incomplete = evaluate_suite_gate(60, 56, 51)
    assert incomplete["passed"] is False
    assert incomplete["missing_report_count"] == 4
    assert incomplete["checks"]["all_planned_reports_present"] is False
    boundary_pass = evaluate_suite_gate(60, 60, 48)
    assert boundary_pass["passed"] is True
    below_rate = evaluate_suite_gate(60, 60, 47)
    assert below_rate["passed"] is False

    print(json.dumps({"status": "pass", "checks": 21}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
