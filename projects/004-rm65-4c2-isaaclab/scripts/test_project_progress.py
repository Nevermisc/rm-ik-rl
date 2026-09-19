#!/usr/bin/env python3
"""Ensure the progress report cannot be completed by one fabricated late-stage file."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        fake_project = Path(temporary)
        results = fake_project / "results"
        results.mkdir()
        (results / "rm65_pi05_real_robot_evaluation.json").write_text(
            json.dumps(
                {
                    "format": "rm65_pi05_real_robot_evaluation_v1",
                    "status": "pass",
                    "robot_model": "RM65-B",
                    "gripper_model": "4C2",
                    "pi05_used": True,
                    "real_robot_command_sent": True,
                    "task_success": True,
                }
            ),
            encoding="utf-8",
        )
        output = results / "progress.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts/build_project_progress.py"),
                "--project-root",
                str(fake_project),
                "--output",
                str(output),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr)
        report = json.loads(output.read_text(encoding="utf-8"))
        assert report["claims"]["pi05_real_robot_task_complete"] is True
        assert report["project_goal_complete"] is False
        assert report["stages"]["pi05_fine_tuning"]["status"] == "not_started"
        assert report["stages"]["pi05_isaaclab_closed_loop"]["status"] != "pass"
    print(
        json.dumps(
            {
                "status": "pass",
                "late_stage_file_cannot_bypass_prerequisites": True,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
