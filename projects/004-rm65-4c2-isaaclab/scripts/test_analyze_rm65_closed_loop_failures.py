#!/usr/bin/env python3
"""Check catastrophic simulation displacement is separated from ordinary task error."""

from __future__ import annotations

import json

from analyze_rm65_closed_loop_failures import failed_criteria, simulation_out_of_bounds


def base_report() -> dict:
    return {
        "all_states_finite": True,
        "source_to_target_xy_distance_m": 0.2,
        "block_lift_height_m": 0.04,
        "final_target_xy_error_m": 0.01,
        "final_target_position_error_m": 0.01,
        "post_release_drift_m": 0.001,
        "final_gripper_normalized": 0.0,
        "final_position_m": [-0.15, -0.18, 0.66],
    }


def main() -> int:
    normal = base_report()
    assert simulation_out_of_bounds(normal) is False
    assert failed_criteria(normal) == []

    fallen = base_report()
    fallen["final_position_m"] = [-4.42, -4.40, -100.61]
    assert simulation_out_of_bounds(fallen) is True
    assert "simulation_out_of_bounds" in failed_criteria(fallen)

    elevated = base_report()
    elevated["final_position_m"] = [0.0, 0.0, 2.01]
    assert simulation_out_of_bounds(elevated) is True

    print(json.dumps({"status": "pass", "checks": 5}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
