#!/usr/bin/env python3
"""Build a training-only scripted-expert plan around primary pi0.5 failures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXACT_REPEAT_COUNT = 3
ANGLE_OFFSETS_RAD = (-0.025, 0.025)
EXPERT_INFEASIBLE_REPLACEMENTS = {
    ("robust_041", "angle_plus_0p025"): {
        "variant": "source_x_inward_0p001875",
        "transfer_angle_delta_rad": 0.0,
        "source_offset_x_delta_m": 0.001875,
        "source_offset_y_delta_m": 0.0,
        "reason": (
            "two exact 0.675 rad attempts and a 0.670 rad diagnostic exceeded "
            "the 0.02 m post-release drift gate; the source-offset replacement "
            "passed without weakening criteria"
        ),
    },
    **{
        ("robust_042", variant): {
            "variant": f"{variant}_source_x_inward_0p00375",
            "transfer_angle_delta_rad": angle_delta,
            "source_offset_x_delta_m": -0.00375,
            "source_offset_y_delta_m": 0.0,
            "reason": (
                "the original +0.01125 m source x and a +0.009375 m probe "
                "crossed an unsafe scripted place-IK branch; +0.0075 m passed "
                "the unchanged 0.75 rad continuity and task-success gates"
            ),
        }
        for variant, angle_delta in (
            ("exact_repeat_1", 0.0),
            ("exact_repeat_2", 0.0),
            ("exact_repeat_3", 0.0),
            ("angle_minus_0p025", -0.025),
            ("angle_plus_0p025", 0.025),
        )
    },
    ("robust_042", "angle_minus_0p025"): {
        "variant": "source_x_inward_0p00525",
        "transfer_angle_delta_rad": 0.0,
        "source_offset_x_delta_m": -0.00525,
        "source_offset_y_delta_m": 0.0,
        "reason": (
            "the repaired-source 0.625 rad task passed IK but caused a physics "
            "escape during place; a 0.65 rad, +0.006 m source-x probe passed "
            "all unchanged task-success gates"
        ),
    },
    ("robust_042", "angle_plus_0p025"): {
        "variant": "source_xy_inward_0p00375_0p001875",
        "transfer_angle_delta_rad": 0.0,
        "source_offset_x_delta_m": -0.00375,
        "source_offset_y_delta_m": 0.001875,
        "reason": (
            "angle variants were removed after the repaired-source 0.625 rad "
            "task caused a physics escape; an orthogonal source-y neighborhood "
            "passed all unchanged task-success gates"
        ),
    },
}


def primary_failure_ids(evidence: dict[str, Any]) -> list[str]:
    cases = evidence.get("cases")
    if not isinstance(cases, list):
        raise ValueError("primary evidence has no cases")
    failures = [case.get("case_id") for case in cases if case.get("status") == "fail"]
    if any(not isinstance(case_id, str) for case_id in failures):
        raise ValueError("primary evidence has an invalid failure case id")
    declared = evidence.get("failure_count")
    if declared != len(failures):
        raise ValueError(
            f"primary evidence failure_count mismatch: {declared} != {len(failures)}"
        )
    if not failures:
        raise ValueError("primary evidence contains no failed cases")
    return failures


def build_plan(
    source_plan: dict[str, Any], primary_evidence: dict[str, Any]
) -> dict[str, Any]:
    source_cases = {
        case["case_id"]: case
        for case in source_plan.get("cases", [])
        if isinstance(case, dict) and isinstance(case.get("case_id"), str)
    }
    failure_ids = primary_failure_ids(primary_evidence)
    missing = sorted(set(failure_ids) - set(source_cases))
    if missing:
        raise ValueError(f"failed cases are missing from source plan: {missing}")

    cases = []
    for source_case_id in failure_ids:
        source = source_cases[source_case_id]
        variants = [
            {
                "variant": f"exact_repeat_{index + 1}",
                "transfer_joint_1_rad": float(source["transfer_joint_1_rad"]),
                "source_offset_x_m": float(source["source_offset_x_m"]),
                "source_offset_y_m": float(source["source_offset_y_m"]),
            }
            for index in range(EXACT_REPEAT_COUNT)
        ]
        variants.extend(
            {
                "variant": f"angle_{'minus' if offset < 0 else 'plus'}_0p025",
                "transfer_joint_1_rad": float(source["transfer_joint_1_rad"])
                + offset,
                "source_offset_x_m": float(source["source_offset_x_m"]),
                "source_offset_y_m": float(source["source_offset_y_m"]),
            }
            for offset in ANGLE_OFFSETS_RAD
        )
        for variant_spec in variants:
            original_variant = variant_spec["variant"]
            replacement = EXPERT_INFEASIBLE_REPLACEMENTS.get(
                (source_case_id, original_variant)
            )
            if replacement is not None:
                variant_spec = {
                    "variant": replacement["variant"],
                    "transfer_joint_1_rad": float(source["transfer_joint_1_rad"])
                    + replacement["transfer_angle_delta_rad"],
                    "source_offset_x_m": float(source["source_offset_x_m"])
                    + replacement["source_offset_x_delta_m"],
                    "source_offset_y_m": float(source["source_offset_y_m"])
                    + replacement["source_offset_y_delta_m"],
                    "replaces_variant": original_variant,
                    "replacement_reason": replacement["reason"],
                }
            index = len(cases)
            case = {
                "case_id": f"correction_{source_case_id}_{variant_spec['variant']}",
                "episode_index": index,
                "split": "train",
                "transfer_joint_1_rad": round(
                    variant_spec["transfer_joint_1_rad"], 6
                ),
                "source_offset_x_m": round(variant_spec["source_offset_x_m"], 6),
                "source_offset_y_m": round(variant_spec["source_offset_y_m"], 6),
                "prompt": source["prompt"],
                "source_evaluation_case_id": source_case_id,
                "variant": variant_spec["variant"],
            }
            if replacement is not None:
                case["replaces_variant"] = variant_spec["replaces_variant"]
                case["replacement_reason"] = variant_spec["replacement_reason"]
            cases.append(case)
    replacement_cases = [case for case in cases if "replaces_variant" in case]
    return {
        "format": "rm65_expert_collection_plan_v1",
        "plan_kind": "rm65_pi05_failure_correction_v1",
        "expert": "scripted",
        "simulation_only": True,
        "pi05_used": False,
        "real_robot_command_sent": False,
        "training_only": True,
        "source_evaluation_plan": source_plan.get("format"),
        "source_primary_evidence_kind": primary_evidence.get("evidence_kind"),
        "source_failure_case_ids": failure_ids,
        "exact_repeat_count_per_source_case": EXACT_REPEAT_COUNT,
        "angle_offsets_rad": list(ANGLE_OFFSETS_RAD),
        "expert_infeasible_replacements": [
            {
                "case_id": case["case_id"],
                "source_evaluation_case_id": case["source_evaluation_case_id"],
                "replaces_variant": case["replaces_variant"],
                "replacement_reason": case["replacement_reason"],
            }
            for case in replacement_cases
        ],
        "case_count": len(cases),
        "train_case_count": len(cases),
        "validation_case_count": 0,
        "independent_confirmation_reuse_allowed": False,
        "cases": cases,
    }


def validate_plan(plan: dict[str, Any]) -> dict[str, Any]:
    cases = plan.get("cases", [])
    source_ids = plan.get("source_failure_case_ids", [])
    expected_per_source = EXACT_REPEAT_COUNT + len(ANGLE_OFFSETS_RAD)
    replacement_cases = [case for case in cases if "replaces_variant" in case]
    checks = {
        "format": plan.get("format") == "rm65_expert_collection_plan_v1",
        "plan_kind": plan.get("plan_kind") == "rm65_pi05_failure_correction_v1",
        "simulation_only": plan.get("simulation_only") is True,
        "no_real_robot_commands": plan.get("real_robot_command_sent") is False,
        "training_only": plan.get("training_only") is True,
        "all_train_split": all(case.get("split") == "train" for case in cases),
        "unique_case_ids": len({case.get("case_id") for case in cases}) == len(cases),
        "contiguous_episode_indices": [case.get("episode_index") for case in cases]
        == list(range(len(cases))),
        "expected_case_count": len(cases) == len(source_ids) * expected_per_source,
        "declared_case_count": plan.get("case_count") == len(cases),
        "angles_within_expert_range": all(
            0.60 <= float(case.get("transfer_joint_1_rad", -1.0)) <= 1.00
            for case in cases
        ),
        "source_case_coverage": all(
            sum(case.get("source_evaluation_case_id") == source_id for case in cases)
            == expected_per_source
            for source_id in source_ids
        ),
        "future_confirmation_reuse_blocked": (
            plan.get("independent_confirmation_reuse_allowed") is False
        ),
        "replacement_cases_declared": len(replacement_cases)
        == len(plan.get("expert_infeasible_replacements", [])),
        "replacement_offsets_within_expert_range": all(
            -0.015 <= float(case.get("source_offset_x_m", 1.0)) <= 0.015
            and -0.015 <= float(case.get("source_offset_y_m", 1.0)) <= 0.015
            for case in replacement_cases
        ),
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "validation_kind": "rm65_pi05_failure_correction_plan_v1",
        "checks": checks,
        "source_failure_case_count": len(source_ids),
        "case_count": len(cases),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-plan", type=Path, required=True)
    parser.add_argument("--primary-evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validation-output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.source_plan.read_text(encoding="utf-8"))
    evidence = json.loads(args.primary_evidence.read_text(encoding="utf-8"))
    plan = build_plan(source, evidence)
    validation = validate_plan(plan)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.validation_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    args.validation_output.write_text(
        json.dumps(validation, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(validation, indent=2))
    return 0 if validation["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
