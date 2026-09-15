#!/usr/bin/env python3
"""Validate and summarize assisted RM65 pick-place development trials."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


EXPECTED_ANGLES = (0.6, 0.8, 1.0)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/pick_place_assisted_robustness.json"),
    )
    args = parser.parse_args()

    result_dir = args.results.resolve()
    trials = [
        load_json(result_dir / f"pick_place_robust_{str(angle).replace('.', 'p')}.json")
        for angle in EXPECTED_ANGLES
    ]

    for expected_angle, trial in zip(EXPECTED_ANGLES, trials, strict=True):
        assert trial["status"] == "pass"
        assert trial["simulation_only"] is True
        assert trial["real_robot_command_sent"] is False
        assert trial["unassisted_full_task_complete"] is False
        assert trial["initialized_at_grasp"] is True
        assert abs(trial["transfer_joint_1_rad"] - expected_angle) < 1e-9
        assert trial["block_lift_height_m"] > 0.02
        assert trial["source_to_target_xy_distance_m"] > 0.12
        assert trial["final_target_position_error_m"] < 0.05
        assert trial["post_release_drift_m"] < 0.02
        assert trial["final_l2_tip_gap_m"] > 0.06
        assistance = trial["development_assistance"]
        assert assistance["source_block_gravity_disabled_until_close"] is True
        assert assistance["target_platform_collision_enabled_after_transfer"] is True
        assert assistance["release_separation_assist_m"] > 0.0

    summary = {
        "status": "pass_with_simulation_assistance",
        "simulation_only": True,
        "real_robot_command_sent": False,
        "pi05_used": False,
        "unassisted_full_task_complete": False,
        "trial_count": len(trials),
        "passed_trials": len(trials),
        "success_rate": 1.0,
        "transfer_joint_1_rad": [trial["transfer_joint_1_rad"] for trial in trials],
        "minimum_block_lift_m": min(trial["block_lift_height_m"] for trial in trials),
        "minimum_transfer_distance_m": min(
            trial["source_to_target_xy_distance_m"] for trial in trials
        ),
        "maximum_final_target_error_m": max(
            trial["final_target_position_error_m"] for trial in trials
        ),
        "maximum_post_release_drift_m": max(
            trial["post_release_drift_m"] for trial in trials
        ),
        "minimum_final_l2_tip_gap_m": min(trial["final_l2_tip_gap_m"] for trial in trials),
        "development_assistance": trials[0]["development_assistance"],
        "interpretation": (
            "The close-lift-transfer-assisted-release-retreat state machine passed at three base "
            "rotation angles. Dynamic approach, natural release, and pi0.5 control remain unvalidated."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
