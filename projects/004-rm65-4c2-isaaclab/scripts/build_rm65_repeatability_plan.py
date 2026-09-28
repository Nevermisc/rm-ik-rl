#!/usr/bin/env python3
"""Build a balanced 20-condition, three-repeat RM65 pi0.5 audit plan."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLAN_FORMAT = "rm65_pi05_sim_evaluation_plan_deterministic_v1"
DEFAULT_MANDATORY_CASE_IDS = (
    "robust_014",
    "robust_028",
    "robust_036",
    "robust_041",
    "robust_042",
    "robust_045",
)
PANEL_TARGETS = {
    "panel_a_inner": 7,
    "panel_b_mid": 7,
    "panel_c_outer": 6,
}


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def build_repeatability_plan(
    source_plan: dict[str, Any],
    mandatory_case_ids: tuple[str, ...] = DEFAULT_MANDATORY_CASE_IDS,
) -> dict[str, Any]:
    source_cases = source_plan.get("cases")
    if not isinstance(source_cases, list) or not source_cases:
        raise ValueError("source plan has no cases")
    by_id = {case["case_id"]: case for case in source_cases}
    missing = sorted(set(mandatory_case_ids) - set(by_id))
    if missing:
        raise ValueError(f"mandatory cases missing from source plan: {missing}")

    cells: dict[tuple[float, str], list[dict[str, Any]]] = defaultdict(list)
    for case in source_cases:
        cells[(case["transfer_joint_1_rad"], case["prompt"])].append(case)
    if len(cells) != 20 or any(len(candidates) != 3 for candidates in cells.values()):
        raise ValueError("source plan must contain three panel candidates for each of 20 angle/prompt cells")

    selected: list[dict[str, Any]] = []
    panel_counts: Counter[str] = Counter()
    panel_order = tuple(PANEL_TARGETS)
    for cell in sorted(cells, key=lambda value: (value[0], value[1])):
        candidates = cells[cell]
        mandatory = [case for case in candidates if case["case_id"] in mandatory_case_ids]
        if len(mandatory) > 1:
            raise ValueError(f"multiple mandatory cases share angle/prompt cell {cell}")
        if mandatory:
            chosen = mandatory[0]
        else:
            eligible = [
                case
                for case in candidates
                if panel_counts[case["panel"]] < PANEL_TARGETS[case["panel"]]
            ]
            if not eligible:
                raise ValueError(f"no remaining panel capacity for cell {cell}")
            chosen = max(
                eligible,
                key=lambda case: (
                    PANEL_TARGETS[case["panel"]] - panel_counts[case["panel"]],
                    -panel_order.index(case["panel"]),
                ),
            )
        selected.append(dict(chosen))
        panel_counts[chosen["panel"]] += 1

    if dict(panel_counts) != PANEL_TARGETS:
        raise ValueError(f"panel targets not met: {dict(panel_counts)}")
    selected.sort(key=lambda case: case["case_id"])
    return {
        "format": PLAN_FORMAT,
        "description": (
            "Preregistered same-condition repeatability audit for frozen RM65 pi0.5 v2. "
            "Run this identical 20-case plan in three independent processes/output roots."
        ),
        "audit_kind": "rm65_pi05_same_seed_repeatability_v1",
        "source_plan_sha256": canonical_sha256(source_plan),
        "preregistration": {
            "created_at": "2026-09-28",
            "repeat_count": 3,
            "identical_plan_per_repeat": True,
            "normal_model_failures_must_not_be_selectively_retried": True,
            "all_repeat_outputs_must_be_preserved": True,
            "mandatory_boundary_case_ids": list(mandatory_case_ids),
        },
        "repeatability_gate": {
            "required_reports": 60,
            "minimum_status_consistency_rate": 0.95,
            "maximum_outcome_flip_cases": 1,
            "require_initial_joint_hash_match": True,
            "require_initial_gripper_hash_match": True,
            "require_chunk_zero_noise_hash_match": True,
            "image_and_action_hash_matches": "reported_but_not_required_until_renderer_fix",
        },
        "frozen_controller_contract": source_plan.get("frozen_controller_contract"),
        "selection_contract": {
            "case_count": 20,
            "one_case_per_angle_prompt_cell": True,
            "panel_targets": PANEL_TARGETS,
            "uses_existing_robustness_seeds_for_same_seed_diagnosis": True,
            "not_an_independent_success_rate_confirmation": True,
        },
        "cases": selected,
    }


def validate_repeatability_plan(plan: dict[str, Any]) -> dict[str, Any]:
    cases = plan.get("cases", [])
    case_ids = [case.get("case_id") for case in cases]
    cells = [(case.get("transfer_joint_1_rad"), case.get("prompt")) for case in cases]
    panels = Counter(case.get("panel") for case in cases)
    angles = Counter(case.get("transfer_joint_1_rad") for case in cases)
    prompts = Counter(case.get("prompt") for case in cases)
    mandatory = plan.get("preregistration", {}).get("mandatory_boundary_case_ids", [])
    checks = {
        "format_supported": plan.get("format") == PLAN_FORMAT,
        "twenty_cases": len(cases) == 20,
        "unique_case_ids": len(set(case_ids)) == len(cases),
        "unique_policy_seeds_within_run": len({case.get("policy_noise_seed") for case in cases}) == len(cases),
        "unique_simulation_seeds_within_run": len({case.get("simulation_seed") for case in cases}) == len(cases),
        "one_case_per_angle_prompt_cell": len(set(cells)) == 20,
        "panel_targets_met": dict(panels) == PANEL_TARGETS,
        "four_angles_balanced": sorted(angles.values()) == [5, 5, 5, 5],
        "five_prompts_balanced": sorted(prompts.values()) == [4, 4, 4, 4, 4],
        "mandatory_cases_present": set(mandatory).issubset(case_ids),
        "three_repeats_preregistered": plan.get("preregistration", {}).get("repeat_count") == 3,
        "ninety_five_percent_consistency_gate": plan.get("repeatability_gate", {}).get("minimum_status_consistency_rate") == 0.95,
    }
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "status": "pass" if not failed else "fail",
        "checks": checks,
        "failed_checks": failed,
        "case_count": len(cases),
        "panel_counts": dict(sorted(panels.items())),
        "angle_counts": {str(key): value for key, value in sorted(angles.items())},
        "prompt_counts": dict(sorted(prompts.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-plan",
        type=Path,
        default=PROJECT_ROOT / "config" / "rm65_pi05_evaluation_plan_robustness_v3_60.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "config" / "rm65_pi05_repeatability_plan_v1_20x3.json",
    )
    parser.add_argument(
        "--validation-output",
        type=Path,
        default=PROJECT_ROOT / "results" / "rm65_pi05_repeatability_plan_v1_20x3_validation.json",
    )
    args = parser.parse_args()
    source_plan = json.loads(args.source_plan.read_text(encoding="utf-8"))
    plan = build_repeatability_plan(source_plan)
    validation = validate_repeatability_plan(plan)
    if validation["status"] != "pass":
        print(json.dumps(validation, indent=2))
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    args.validation_output.parent.mkdir(parents=True, exist_ok=True)
    args.validation_output.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(validation, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
