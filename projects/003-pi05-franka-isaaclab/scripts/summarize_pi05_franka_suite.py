"""汇总指定的 π0.5 Franka 基线与鲁棒性评测结果。"""

from __future__ import annotations

import json
import os
from pathlib import Path


SIM_EVALS_DIR = Path(
    os.environ.get("SIM_EVALS_DIR", Path.home() / "robot-learning" / "sim-evals")
)
ROOT = SIM_EVALS_DIR / "runs" / "pi05_franka_suite"
RUNS = {
    "baseline_scene1": ROOT / "20260914_173721/scene_1/scene_summary.json",
    "baseline_scene2": ROOT / "20260914_174248/scene_2/scene_summary.json",
    "baseline_scene3": ROOT / "20260914_174916/scene_3/scene_summary.json",
    "robust_scene1": ROOT / "20260914_175634/scene_1/scene_summary.json",
    "robust_scene2": ROOT / "20260914_180441/scene_2/scene_summary.json",
    "robust_scene3": ROOT / "20260914_181627/scene_3/scene_summary.json",
}


records = []
groups = []
for group, path in RUNS.items():
    data = json.loads(path.read_text())
    groups.append(
        {
            "group": group,
            "scene": data["scene"],
            "suite": data["suite"],
            "successful": data["cases_successful"],
            "total": data["cases_total"],
            "remote_directory": str(path.parent),
        }
    )
    for case in data["cases"]:
        records.append(
            {
                "group": group,
                "scene": case["scene"],
                "case": case["case"]["name"],
                "prompt": case["case"]["prompt"],
                "success": case["success"],
                "steps": case["steps"],
                "elapsed_seconds": case["elapsed_seconds"],
                "source_displacement_m": case["source_displacement_m"],
                "final_source_target_xy_m": case["final_source_target_xy_m"],
                "final_gripper_observed": case["final_gripper_observed"],
                "entered_target_while_closed": case["entered_target_while_closed"],
            }
        )

baseline = [r for r in records if r["group"].startswith("baseline")]
robustness = [r for r in records if r["group"].startswith("robust")]
report = {
    "strict_success_definition": "source in target, observed gripper open, stable for 15 steps",
    "baseline": {
        "successful": sum(r["success"] for r in baseline),
        "total": len(baseline),
    },
    "robustness": {
        "successful": sum(r["success"] for r in robustness),
        "total": len(robustness),
    },
    "overall": {
        "successful": sum(r["success"] for r in records),
        "total": len(records),
    },
    "groups": groups,
    "failures": [r for r in records if not r["success"]],
    "cases": records,
}

output = ROOT / "pi05_franka_robustness_report_20260914.json"
output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
print(f"REPORT_PATH={output}")
