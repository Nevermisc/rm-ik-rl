#!/usr/bin/env python3
"""Verify that the RM65 closed-loop suite uses held-out interpolation cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-plan", type=Path, required=True)
    parser.add_argument("--evaluation-plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    collection = json.loads(args.collection_plan.read_text(encoding="utf-8"))
    evaluation = json.loads(args.evaluation_plan.read_text(encoding="utf-8"))
    demonstrations = collection["cases"]
    cases = evaluation["cases"]

    keys = ("transfer_joint_1_rad", "source_offset_x_m", "source_offset_y_m")
    demo_conditions = {tuple(case[key] for key in keys) for case in demonstrations}
    eval_conditions = [tuple(case[key] for key in keys) for case in cases]
    demo_angles = {case["transfer_joint_1_rad"] for case in demonstrations}
    eval_angles = {case["transfer_joint_1_rad"] for case in cases}
    demo_prompts = {case["prompt"] for case in demonstrations}
    eval_prompts = {case["prompt"] for case in cases}

    angle_min = min(demo_angles)
    angle_max = max(demo_angles)
    x_values = [case["source_offset_x_m"] for case in demonstrations]
    y_values = [case["source_offset_y_m"] for case in demonstrations]
    checks = {
        "collection_format": collection.get("format") == "rm65_expert_collection_plan_v1",
        "evaluation_format": evaluation.get("format")
        == "rm65_pi05_sim_evaluation_plan_v1",
        "twenty_evaluation_cases": len(cases) == 20,
        "unique_case_ids": len({case["case_id"] for case in cases}) == len(cases),
        "unique_evaluation_conditions": len(set(eval_conditions)) == len(cases),
        "all_full_conditions_held_out": all(
            condition not in demo_conditions for condition in eval_conditions
        ),
        "all_transfer_angles_held_out": eval_angles.isdisjoint(demo_angles),
        "angles_inside_demonstration_range": all(
            angle_min < angle < angle_max for angle in eval_angles
        ),
        "offsets_inside_demonstration_range": all(
            min(x_values) <= case["source_offset_x_m"] <= max(x_values)
            and min(y_values) <= case["source_offset_y_m"] <= max(y_values)
            for case in cases
        ),
        "contains_seen_prompts": bool(eval_prompts & demo_prompts),
        "contains_novel_prompt_wordings": bool(eval_prompts - demo_prompts),
    }
    failed = [name for name, passed in checks.items() if not passed]
    report = {
        "status": "pass" if not failed else "fail",
        "evaluation_kind": "held_out_interpolation",
        "checks": checks,
        "failed_checks": failed,
        "demonstration_case_count": len(demonstrations),
        "evaluation_case_count": len(cases),
        "demonstration_transfer_angles_rad": sorted(demo_angles),
        "evaluation_transfer_angles_rad": sorted(eval_angles),
        "demonstration_offset_range_m": {
            "x": [min(x_values), max(x_values)],
            "y": [min(y_values), max(y_values)],
        },
        "evaluation_offsets_m": {
            "x": sorted({case["source_offset_x_m"] for case in cases}),
            "y": sorted({case["source_offset_y_m"] for case in cases}),
        },
        "seen_prompt_count": len(eval_prompts & demo_prompts),
        "novel_prompt_count": len(eval_prompts - demo_prompts),
        "novel_prompts": sorted(eval_prompts - demo_prompts),
        "interpretation": (
            "Every kinematic evaluation tuple is absent from demonstrations while "
            "remaining inside their sampled range; this tests interpolation, not "
            "out-of-distribution extrapolation."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
