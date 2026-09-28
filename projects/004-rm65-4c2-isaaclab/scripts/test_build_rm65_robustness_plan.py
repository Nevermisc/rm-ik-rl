#!/usr/bin/env python3
"""Tests for the preregistered RM65 pi0.5 robustness plan builder."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("build_rm65_robustness_plan.py")
SPEC = importlib.util.spec_from_file_location("build_rm65_robustness_plan", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def collection_plan() -> dict:
    cases = []
    for angle in (0.6, 0.7, 0.8, 0.9, 1.0):
        for offset_x in (-0.015, 0.0, 0.015):
            for offset_y in (-0.015, 0.0, 0.015):
                cases.append(
                    {
                        "transfer_joint_1_rad": angle,
                        "source_offset_x_m": offset_x,
                        "source_offset_y_m": offset_y,
                    }
                )
    return {"cases": cases}


class RobustnessPlanTest(unittest.TestCase):
    def test_plan_is_balanced_and_held_out(self) -> None:
        plan = MODULE.build_plan(490928000, 590928000)
        validation = MODULE.validate_plan(plan, collection_plan(), [])
        self.assertEqual(validation["status"], "pass")
        self.assertEqual(validation["case_count"], 60)
        self.assertEqual(sorted(validation["panel_counts"].values()), [20, 20, 20])
        self.assertEqual(sorted(validation["prompt_counts"].values()), [12] * 5)

    def test_prior_seed_overlap_is_rejected(self) -> None:
        plan = MODULE.build_plan(490928000, 590928000)
        prior = {
            "cases": [
                {
                    "policy_noise_seed": 490928010,
                    "simulation_seed": 590928020,
                }
            ]
        }
        validation = MODULE.validate_plan(plan, collection_plan(), [prior])
        self.assertEqual(validation["status"], "fail")
        self.assertIn(
            "policy_seeds_disjoint_from_prior_plans", validation["failed_checks"]
        )
        self.assertIn(
            "simulation_seeds_disjoint_from_prior_plans",
            validation["failed_checks"],
        )


if __name__ == "__main__":
    unittest.main()
