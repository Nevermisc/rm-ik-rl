#!/usr/bin/env python3
"""Aggregate the three gravity-enabled 4C2 transport perturbation trials."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


TRIAL_FILES = {
    "width_axis_minus_2mm": ("gripper_contact_transport_offset_neg2mm.json", -0.002),
    "center": ("gripper_contact_transport.json", 0.0),
    "width_axis_plus_2mm": ("gripper_contact_transport_offset_pos2mm.json", 0.002),
}


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--output", type=Path, default=Path("results/gripper_transport_robustness.json"))
    args = parser.parse_args()

    result_dir = args.results.resolve()
    rows = []
    for name, (filename, expected_offset) in TRIAL_FILES.items():
        trial = load(result_dir / filename)
        offset = trial.get("contact_block_width_axis_offset_m", expected_offset)
        passed = (
            trial["status"] == "pass"
            and trial["block_gravity_enabled_during_transport"] is True
            and trial["actual_tool_lift_m"] > 0.03
            and trial["actual_cube_lift_m"] > 0.02
            and trial["cube_to_tool_relative_position_change_m"] < 0.04
            and trial["cube_state_finite"] is True
        )
        rows.append(
            {
                "name": name,
                "passed": passed,
                "block_width_axis_offset_m": offset,
                "tool_lift_m": trial["actual_tool_lift_m"],
                "block_lift_m": trial["actual_cube_lift_m"],
                "block_to_tool_relative_position_change_m": trial[
                    "cube_to_tool_relative_position_change_m"
                ],
                "transport_duration_s": trial.get("transport_duration_s", 1.0),
            }
        )

    passed_trials = sum(row["passed"] for row in rows)
    report = {
        "status": "pass" if passed_trials == len(rows) else "fail",
        "simulation_only": True,
        "gravity_enabled_during_transport": True,
        "trial_count": len(rows),
        "passed_trials": passed_trials,
        "success_rate": passed_trials / len(rows),
        "minimum_tool_lift_m": min(row["tool_lift_m"] for row in rows),
        "minimum_block_lift_m": min(row["block_lift_m"] for row in rows),
        "maximum_block_to_tool_relative_position_change_m": max(
            row["block_to_tool_relative_position_change_m"] for row in rows
        ),
        "criteria": {
            "tool_lift_m_gt": 0.03,
            "block_lift_m_gt": 0.02,
            "block_to_tool_relative_position_change_m_lt": 0.04,
            "all_states_finite": True,
        },
        "trials": rows,
        "limitation": (
            "The 30 g block starts suspended between empirically placed collision pads; "
            "the benchmark does not yet include table pickup, release, or pi0.5 closed-loop control."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
