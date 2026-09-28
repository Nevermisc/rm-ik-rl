#!/usr/bin/env python3
"""Unit checks for the preregistered RM65 v3 confirmation plan."""

from __future__ import annotations

import json

from build_rm65_v3_confirmation_plan import build_plan, validate_plan


def main() -> int:
    plan = build_plan(1000, 2000)
    training = {
        "cases": [
            {
                "transfer_joint_1_rad": 0.6,
                "source_offset_x_m": -0.015,
                "source_offset_y_m": -0.015,
            }
        ]
    }
    prior = {
        "cases": [
            {
                "transfer_joint_1_rad": 0.65,
                "source_offset_x_m": 0.0,
                "source_offset_y_m": 0.0,
                "policy_noise_seed": 10,
                "simulation_seed": 20,
            }
        ]
    }
    validation = validate_plan(plan, [training], [prior])
    assert validation["status"] == "pass"
    assert validation["case_count"] == 20
    assert all(validation["checks"].values())
    contaminated_training = {"cases": [dict(plan["cases"][0])]}
    contaminated = validate_plan(plan, [contaminated_training], [prior])
    assert contaminated["status"] == "fail"
    assert not contaminated["checks"]["conditions_held_out_from_training"]
    assert not contaminated["checks"]["angles_held_out_from_training"]
    contaminated_prior = {"cases": [dict(plan["cases"][1])]}
    reused = validate_plan(plan, [training], [contaminated_prior])
    assert reused["status"] == "fail"
    assert not reused["checks"]["conditions_held_out_from_prior_evaluation"]
    assert not reused["checks"]["policy_seeds_held_out"]
    assert not reused["checks"]["simulation_seeds_held_out"]
    print(json.dumps({"status": "pass", "checks": 10}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

