"""汇总三次 Franka 工程审计并排除超时自动重置造成的假跳变。"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np


SIM_EVALS_DIR = Path(
    os.environ.get("SIM_EVALS_DIR", Path.home() / "robot-learning" / "sim-evals")
)
ROOT = SIM_EVALS_DIR / "runs" / "pi05_franka_suite"
RUNS = {
    "scene_1": ROOT / "20260914_182910/scene_1/01_engineering_audit",
    "scene_2": ROOT / "20260914_183231/scene_2/01_engineering_audit",
    "scene_3": ROOT / "20260914_183626/scene_3/01_engineering_audit",
}

report = {}
for scene, case_dir in RUNS.items():
    summary = json.loads((case_dir / "summary.json").read_text())
    trajectory = np.load(case_dir / "trajectory.npz")
    observed = trajectory["arm_observed"]
    terminal_reset_removed = False
    if len(observed) > 1 and np.max(np.abs(observed[-1] - observed[-2])) > 0.5:
        observed = observed[:-1]
        terminal_reset_removed = True
    observed_jump = float(np.max(np.abs(np.diff(observed, axis=0))))
    report[scene] = {
        "task_success": summary["success"],
        "steps": summary["steps"],
        "terminal_auto_reset_sample_removed": terminal_reset_removed,
        "action_all_finite": summary["safety_and_performance"]["action_all_finite"],
        "observation_all_finite": bool(np.isfinite(observed).all()),
        "minimum_observed_joint_limit_margin_rad": summary["safety_and_performance"][
            "minimum_observed_joint_limit_margin_rad"
        ],
        "maximum_command_step_jump_rad": summary["safety_and_performance"][
            "maximum_command_step_jump_rad"
        ],
        "maximum_observed_joint_step_jump_rad": observed_jump,
        "replan_count": summary["safety_and_performance"]["replan_count"],
        "inference_latency_median_seconds": summary["safety_and_performance"][
            "inference_latency_median_seconds"
        ],
        "inference_latency_p95_seconds": summary["safety_and_performance"][
            "inference_latency_p95_seconds"
        ],
        "inference_latency_max_seconds": summary["safety_and_performance"][
            "inference_latency_max_seconds"
        ],
    }

output = ROOT / "pi05_franka_engineering_audit_20260914.json"
output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
print(f"REPORT_PATH={output}")
