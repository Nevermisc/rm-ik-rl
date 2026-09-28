#!/usr/bin/env python3
"""Unit tests for the balanced RM65 repeatability plan builder."""

from __future__ import annotations

import json

from build_rm65_repeatability_plan import build_repeatability_plan
from build_rm65_repeatability_plan import validate_repeatability_plan


def synthetic_source() -> dict:
    cases = []
    index = 0
    for panel in ("panel_a_inner", "panel_b_mid", "panel_c_outer"):
        for angle in (0.65, 0.75, 0.85, 0.95):
            for prompt_index in range(5):
                cases.append(
                    {
                        "case_id": f"case_{index:03d}",
                        "panel": panel,
                        "policy_noise_seed": 1000 + index,
                        "simulation_seed": 2000 + index,
                        "transfer_joint_1_rad": angle,
                        "source_offset_x_m": float(prompt_index),
                        "source_offset_y_m": float(-prompt_index),
                        "prompt": f"prompt_{prompt_index}",
                    }
                )
                index += 1
    return {"format": "rm65_pi05_sim_evaluation_plan_deterministic_v1", "cases": cases}


def main() -> int:
    source = synthetic_source()
    mandatory = (
        "case_000",
        "case_021",
        "case_042",
        "case_008",
        "case_029",
        "case_050",
    )
    plan = build_repeatability_plan(source, mandatory)
    validation = validate_repeatability_plan(plan)
    assert validation["status"] == "pass"
    assert validation["case_count"] == 20
    assert validation["panel_counts"] == {
        "panel_a_inner": 7,
        "panel_b_mid": 7,
        "panel_c_outer": 6,
    }
    assert set(mandatory).issubset(case["case_id"] for case in plan["cases"])
    assert plan["preregistration"]["repeat_count"] == 3
    assert plan["repeatability_gate"]["minimum_status_consistency_rate"] == 0.95

    try:
        build_repeatability_plan(source, ("missing",))
    except ValueError as error:
        assert "missing" in str(error)
    else:
        raise AssertionError("missing mandatory case must be rejected")

    print(json.dumps({"status": "pass", "checks": 7}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
