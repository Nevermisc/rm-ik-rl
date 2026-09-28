#!/usr/bin/env python3
"""Unit checks for the RM65 failure-correction expert plan."""

from __future__ import annotations

import json

from build_rm65_failure_correction_plan import build_plan, validate_plan


def main() -> int:
    source = {
        "format": "source",
        "cases": [
            {
                "case_id": "failed_a",
                "transfer_joint_1_rad": 0.65,
                "source_offset_x_m": 0.01,
                "source_offset_y_m": -0.01,
                "prompt": "move the block",
            },
            {
                "case_id": "passed_b",
                "transfer_joint_1_rad": 0.95,
                "source_offset_x_m": 0.0,
                "source_offset_y_m": 0.0,
                "prompt": "pick the block",
            },
        ],
    }
    evidence = {
        "evidence_kind": "primary",
        "failure_count": 1,
        "cases": [
            {"case_id": "failed_a", "status": "fail"},
            {"case_id": "passed_b", "status": "pass"},
        ],
    }
    plan = build_plan(source, evidence)
    validation = validate_plan(plan)
    assert validation["status"] == "pass"
    assert plan["case_count"] == 5
    assert plan["source_failure_case_ids"] == ["failed_a"]
    assert all(case["split"] == "train" for case in plan["cases"])
    assert [case["transfer_joint_1_rad"] for case in plan["cases"]][-2:] == [
        0.625,
        0.675,
    ]
    assert len({case["case_id"] for case in plan["cases"]}) == 5
    assert plan["independent_confirmation_reuse_allowed"] is False

    replacement_source = {
        "format": "source",
        "cases": [
            {
                "case_id": "robust_041",
                "transfer_joint_1_rad": 0.65,
                "source_offset_x_m": -0.01125,
                "source_offset_y_m": 0.01125,
                "prompt": "pick up the block",
            },
            {
                "case_id": "robust_042",
                "transfer_joint_1_rad": 0.65,
                "source_offset_x_m": 0.01125,
                "source_offset_y_m": -0.01125,
                "prompt": "move the block",
            },
        ],
    }
    replacement_evidence = {
        "evidence_kind": "primary",
        "failure_count": 2,
        "cases": [
            {"case_id": "robust_041", "status": "fail"},
            {"case_id": "robust_042", "status": "fail"},
        ],
    }
    replacement_plan = build_plan(replacement_source, replacement_evidence)
    replacement_case = next(
        case
        for case in replacement_plan["cases"]
        if case["source_evaluation_case_id"] == "robust_041"
        and case.get("replaces_variant") == "angle_plus_0p025"
    )
    assert replacement_case["variant"] == "source_x_inward_0p001875"
    assert replacement_case["replaces_variant"] == "angle_plus_0p025"
    assert replacement_case["transfer_joint_1_rad"] == 0.65
    assert replacement_case["source_offset_x_m"] == -0.009375
    assert validate_plan(replacement_plan)["status"] == "pass"
    robust_042_cases = [
        case
        for case in replacement_plan["cases"]
        if case["source_evaluation_case_id"] == "robust_042"
    ]
    assert len(robust_042_cases) == 5
    assert all(case["transfer_joint_1_rad"] == 0.65 for case in robust_042_cases)
    assert [
        [case["source_offset_x_m"], case["source_offset_y_m"]]
        for case in robust_042_cases
    ] == [
        [0.0075, -0.01125],
        [0.0075, -0.01125],
        [0.0075, -0.01125],
        [0.006, -0.01125],
        [0.0075, -0.009375],
    ]

    bad_evidence = {**evidence, "failure_count": 2}
    try:
        build_plan(source, bad_evidence)
    except ValueError:
        pass
    else:
        raise AssertionError("mismatched failure_count must fail closed")
    print(json.dumps({"status": "pass", "checks": 17}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
