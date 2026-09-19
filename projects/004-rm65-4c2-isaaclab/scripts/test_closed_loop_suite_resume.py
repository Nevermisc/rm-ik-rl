#!/usr/bin/env python3
"""Verify resumable evaluation never mixes reports from different gripper thresholds."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from run_pi05_rm65_closed_loop_suite import load_existing_report


def write_report(path: Path, threshold: float | None, *, historical: bool = False) -> None:
    report = {
        "policy_checkpoint_id": "experiment/29999",
        "pi05_used": True,
        "simulation_only": True,
    }
    if historical:
        report["criteria"] = {"final_gripper_normalized_lt": threshold}
    elif threshold is not None:
        report["controller_config"] = {"policy_gripper_open_threshold": threshold}
    path.write_text(json.dumps(report), encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "task_report.json"
        write_report(path, 0.20)
        assert load_existing_report(path, "experiment/29999", 0.20) is not None
        assert load_existing_report(path, "experiment/29999", 0.12) is None

        write_report(path, 0.12, historical=True)
        assert load_existing_report(path, "experiment/29999", 0.12) is not None
        assert load_existing_report(path, "experiment/29999", 0.20) is None

        write_report(path, None)
        assert load_existing_report(path, "experiment/29999", 0.12) is None

    print(json.dumps({"status": "pass", "checks": 5}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
