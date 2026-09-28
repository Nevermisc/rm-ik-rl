#!/usr/bin/env python3
"""Build a training-only scripted-expert plan around primary pi0.5 failures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXACT_REPEAT_COUNT = 3
ANGLE_OFFSETS_RAD = (-0.025, 0.025)


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
            (f"exact_repeat_{index + 1}", float(source["transfer_joint_1_rad"]))
            for index in range(EXACT_REPEAT_COUNT)
        ]
        variants.extend(
            (
                f"angle_{'minus' if offset < 0 else 'plus'}_0p025",
                float(source["transfer_joint_1_rad"]) + offset,
            )
            for offset in ANGLE_OFFSETS_RAD
        )
        for variant, angle in variants:
            index = len(cases)
            cases.append(
                {
                    "case_id": f"correction_{source_case_id}_{variant}",
                    "episode_index": index,
                    "split": "train",
                    "transfer_joint_1_rad": round(angle, 6),
                    "source_offset_x_m": float(source["source_offset_x_m"]),
                    "source_offset_y_m": float(source["source_offset_y_m"]),
                    "prompt": source["prompt"],
                    "source_evaluation_case_id": source_case_id,
                    "variant": variant,
                }
            )
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
