#!/usr/bin/env python3
"""Compare repeated RM65 pi0.5 simulation runs without hiding outcome flips."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


OBSERVATION_CHANNELS = (
    "joint_position",
    "gripper_position",
    "external_image",
    "wrist_image",
)


def load_report(root: Path, case_id: str) -> dict[str, Any] | None:
    path = root / case_id / "task_report.json"
    if not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"task report must be an object: {path}")
    return value


def sampling_chunks(report: dict[str, Any]) -> list[dict[str, Any]]:
    sampling = report.get("deterministic_sampling")
    chunks = sampling.get("chunks") if isinstance(sampling, dict) else None
    if not isinstance(chunks, list) or not all(isinstance(chunk, dict) for chunk in chunks):
        return []
    return chunks


def matching_prefix_length(
    reference_chunks: list[dict[str, Any]],
    candidate_chunks: list[dict[str, Any]],
    keys: tuple[str, ...],
) -> int:
    count = 0
    for reference, candidate in zip(reference_chunks, candidate_chunks):
        if any(reference.get(key) != candidate.get(key) for key in keys):
            break
        count += 1
    return count


def compare_reports(
    case: dict[str, Any],
    reference: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    reference_chunks = sampling_chunks(reference)
    candidate_chunks = sampling_chunks(candidate)
    reference_first = reference_chunks[0] if reference_chunks else {}
    candidate_first = candidate_chunks[0] if candidate_chunks else {}
    reference_observation = reference_first.get("observation_sha256", {})
    candidate_observation = candidate_first.get("observation_sha256", {})
    if not isinstance(reference_observation, dict):
        reference_observation = {}
    if not isinstance(candidate_observation, dict):
        candidate_observation = {}

    initial_observation_matches = {
        channel: (
            reference_observation.get(channel) is not None
            and reference_observation.get(channel) == candidate_observation.get(channel)
        )
        for channel in OBSERVATION_CHANNELS
    }
    common_chunk_count = min(len(reference_chunks), len(candidate_chunks))
    noise_prefix = matching_prefix_length(reference_chunks, candidate_chunks, ("noise_sha256",))
    action_prefix = matching_prefix_length(
        reference_chunks,
        candidate_chunks,
        ("raw_action_sha256", "safe_action_sha256"),
    )
    observation_prefix = matching_prefix_length(
        reference_chunks,
        candidate_chunks,
        ("observation_sha256",),
    )
    status_match = reference.get("status") == candidate.get("status")
    strict_repeatability = bool(
        status_match
        and len(reference_chunks) == len(candidate_chunks)
        and common_chunk_count > 0
        and noise_prefix == common_chunk_count
        and observation_prefix == common_chunk_count
        and action_prefix == common_chunk_count
    )
    return {
        "case_id": case["case_id"],
        "panel": case.get("panel"),
        "policy_noise_seed": case.get("policy_noise_seed"),
        "simulation_seed": case.get("simulation_seed"),
        "reference_status": reference.get("status"),
        "candidate_status": candidate.get("status"),
        "status_match": status_match,
        "outcome_flip": not status_match,
        "reference_action_chunks": reference.get("action_chunks"),
        "candidate_action_chunks": candidate.get("action_chunks"),
        "initial_observation_matches": initial_observation_matches,
        "initial_noise_match": (
            reference_first.get("noise_sha256") is not None
            and reference_first.get("noise_sha256") == candidate_first.get("noise_sha256")
        ),
        "initial_raw_action_match": (
            reference_first.get("raw_action_sha256") is not None
            and reference_first.get("raw_action_sha256")
            == candidate_first.get("raw_action_sha256")
        ),
        "common_chunk_count": common_chunk_count,
        "matching_noise_prefix_chunks": noise_prefix,
        "matching_observation_prefix_chunks": observation_prefix,
        "matching_action_prefix_chunks": action_prefix,
        "strict_repeatability_verified": strict_repeatability,
        "metrics": {
            "reference": {
                "block_lift_height_m": reference.get("block_lift_height_m"),
                "final_target_position_error_m": reference.get("final_target_position_error_m"),
                "final_gripper_normalized": reference.get("final_gripper_normalized"),
            },
            "candidate": {
                "block_lift_height_m": candidate.get("block_lift_height_m"),
                "final_target_position_error_m": candidate.get("final_target_position_error_m"),
                "final_gripper_normalized": candidate.get("final_gripper_normalized"),
            },
        },
    }


def build_analysis(
    plan: dict[str, Any],
    reference_root: Path,
    candidate_root: Path,
) -> dict[str, Any]:
    cases = plan.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("evaluation plan has no cases")

    comparisons: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("case_id"), str):
            raise ValueError("every evaluation case must have a string case_id")
        case_id = case["case_id"]
        reference = load_report(reference_root, case_id)
        candidate = load_report(candidate_root, case_id)
        if reference is None or candidate is None:
            missing.append(
                {
                    "case_id": case_id,
                    "reference_report_present": reference is not None,
                    "candidate_report_present": candidate is not None,
                }
            )
            continue
        comparisons.append(compare_reports(case, reference, candidate))

    channel_match_counts = {
        channel: sum(
            comparison["initial_observation_matches"][channel]
            for comparison in comparisons
        )
        for channel in OBSERVATION_CHANNELS
    }
    strict_repeatability = bool(
        not missing
        and len(comparisons) == len(cases)
        and all(comparison["strict_repeatability_verified"] for comparison in comparisons)
    )
    return {
        "status": "pass",
        "analysis_kind": "rm65_pi05_repeatability_audit",
        "simulation_only": True,
        "real_robot_command_sent": False,
        "planned_case_count": len(cases),
        "comparable_case_count": len(comparisons),
        "missing_case_count": len(missing),
        "outcome_flip_count": sum(comparison["outcome_flip"] for comparison in comparisons),
        "status_match_count": sum(comparison["status_match"] for comparison in comparisons),
        "initial_observation_match_counts": channel_match_counts,
        "initial_noise_match_count": sum(
            comparison["initial_noise_match"] for comparison in comparisons
        ),
        "initial_raw_action_match_count": sum(
            comparison["initial_raw_action_match"] for comparison in comparisons
        ),
        "strict_repeatability_verified": strict_repeatability,
        "end_to_end_determinism_claim_supported": strict_repeatability,
        "interpretation": (
            "Explicit policy noise seeds can be reproducible while rendered observations, "
            "policy actions, trajectories, and outcomes remain non-repeatable."
        ),
        "missing_cases": missing,
        "cases": comparisons,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    analysis = build_analysis(plan, args.reference_root, args.candidate_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in analysis.items() if key != "cases"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
