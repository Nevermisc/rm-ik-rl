#!/usr/bin/env python3
"""Regression checks for evidence-driven RM65 v5 plans."""

from __future__ import annotations

import json
from pathlib import Path

from build_rm65_v5_plans import (
    CORRECTION_FOCUS_BY_CASE,
    build_confirmation_plan,
    build_correction_plan,
    validate_confirmation_plan,
    validate_correction_plan,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load(relative: str) -> dict:
    return json.loads((PROJECT_ROOT / relative).read_text(encoding="utf-8"))


def main() -> int:
    source = load("config/rm65_pi05_failure_correction_v4_confirmation_20.json")
    repeatability = load("results/rm65_pi05_failure_correction_v4_repeatability_20x3.json")
    base = load("config/rm65_expert_collection_plan_v1.json")
    v3_correction = load("config/rm65_pi05_failure_correction_expert_plan_v1.json")
    v4_correction = load("config/rm65_pi05_failure_correction_v4_expert_plan.json")
    v3_confirmation = load("config/rm65_pi05_failure_correction_v3_confirmation_20.json")
    correction = build_correction_plan(source, repeatability)
    correction_validation = validate_correction_plan(correction)
    confirmation = build_confirmation_plan(692029000, 792029000)
    confirmation_validation = validate_confirmation_plan(
        confirmation,
        [base, v3_correction, v4_correction, correction],
        [v3_confirmation, source],
    )
    selected = correction["source_failure_or_flip_case_ids"]
    passed = (
        correction_validation["status"] == "pass"
        and confirmation_validation["status"] == "pass"
        and set(selected) == set(CORRECTION_FOCUS_BY_CASE)
        and correction["case_count"] == 48
        and len({case["simulation_seed"] for case in correction["cases"]}) == 12
        and len(confirmation["cases"]) == 20
    )
    print("RM65_V5_PLAN_TEST=PASS" if passed else "RM65_V5_PLAN_TEST=FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
