#!/usr/bin/env python3
"""Aggregate the five static 4C2 contact-pad perturbation trials."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


TRIAL_FILES = {
    "center": "gripper_contact_pads_center.json",
    "width_axis_minus_2mm": "contact_pads_offset_neg2mm.json",
    "width_axis_plus_2mm": "contact_pads_offset_pos2mm.json",
    "outward_8mm": "contact_pads_outward_8mm.json",
    "outward_12mm": "contact_pads_outward_12mm.json",
}


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--output", type=Path, default=Path("results/gripper_contact_pad_robustness.json"))
    args = parser.parse_args()

    result_dir = args.results.resolve()
    trials = {name: load(result_dir / filename) for name, filename in TRIAL_FILES.items()}
    rows = []
    for name, trial in trials.items():
        base_force = trial["cube_contact_force_by_gripper_body_n"]["tool_base_link"]
        passed = (
            trial["status"] == "pass"
            and trial["bilateral_fingertip_contact_confirmed"] is True
            and trial["left_finger_contact_force_n"] > 0.05
            and trial["right_finger_contact_force_n"] > 0.05
            and base_force < 0.01
            and trial["cube_displacement_during_close_m"] < 0.002
        )
        rows.append(
            {
                "name": name,
                "passed": passed,
                "block_inward_offset_m": trial["contact_block_inward_offset_m"],
                "block_width_axis_offset_m": trial.get("contact_block_width_axis_offset_m", 0.0),
                "left_finger_contact_force_n": trial["left_finger_contact_force_n"],
                "right_finger_contact_force_n": trial["right_finger_contact_force_n"],
                "base_contact_force_n": base_force,
                "block_displacement_m": trial["cube_displacement_during_close_m"],
            }
        )

    passed_trials = sum(row["passed"] for row in rows)
    report = {
        "status": "pass" if passed_trials == len(rows) else "fail",
        "simulation_only": True,
        "static_contact_only": True,
        "trial_count": len(rows),
        "passed_trials": passed_trials,
        "success_rate": passed_trials / len(rows),
        "minimum_left_finger_contact_force_n": min(row["left_finger_contact_force_n"] for row in rows),
        "minimum_right_finger_contact_force_n": min(row["right_finger_contact_force_n"] for row in rows),
        "maximum_base_contact_force_n": max(row["base_contact_force_n"] for row in rows),
        "maximum_block_displacement_m": max(row["block_displacement_m"] for row in rows),
        "criteria": {
            "bilateral_fingertip_contact_confirmed": True,
            "each_finger_contact_force_n_gt": 0.05,
            "base_contact_force_n_lt": 0.01,
            "block_displacement_m_lt": 0.002,
        },
        "trials": rows,
        "limitation": "The block is gravity-disabled and the result covers static closing only.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
