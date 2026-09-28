#!/usr/bin/env python3
"""Unit tests for the RM65 pi0.5 repeatability audit."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from analyze_rm65_repeatability import build_analysis


def report(status: str, image_hash: str, action_hash: str) -> dict:
    return {
        "status": status,
        "action_chunks": 1,
        "deterministic_sampling": {
            "chunks": [
                {
                    "noise_sha256": "same-noise",
                    "observation_sha256": {
                        "joint_position": "same-joints",
                        "gripper_position": "same-gripper",
                        "external_image": image_hash,
                        "wrist_image": image_hash,
                    },
                    "raw_action_sha256": action_hash,
                    "safe_action_sha256": action_hash,
                }
            ]
        },
    }


def write_report(root: Path, case_id: str, value: dict) -> None:
    case_dir = root / case_id
    case_dir.mkdir(parents=True)
    (case_dir / "task_report.json").write_text(json.dumps(value), encoding="utf-8")


def main() -> int:
    plan = {
        "cases": [
            {"case_id": "same", "policy_noise_seed": 1, "simulation_seed": 11},
            {"case_id": "flip", "policy_noise_seed": 2, "simulation_seed": 12},
        ]
    }
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        reference = root / "reference"
        candidate = root / "candidate"
        write_report(reference, "same", report("pass", "image-a", "action-a"))
        write_report(candidate, "same", report("pass", "image-a", "action-a"))
        write_report(reference, "flip", report("fail", "image-a", "action-a"))
        write_report(candidate, "flip", report("pass", "image-b", "action-b"))

        analysis = build_analysis(plan, reference, candidate)
        assert analysis["status"] == "pass"
        assert analysis["comparable_case_count"] == 2
        assert analysis["outcome_flip_count"] == 1
        assert analysis["initial_noise_match_count"] == 2
        assert analysis["initial_raw_action_match_count"] == 1
        assert analysis["initial_observation_match_counts"]["joint_position"] == 2
        assert analysis["initial_observation_match_counts"]["external_image"] == 1
        assert not analysis["strict_repeatability_verified"]
        assert not analysis["end_to_end_determinism_claim_supported"]

    print(json.dumps({"status": "pass", "checks": 10}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
