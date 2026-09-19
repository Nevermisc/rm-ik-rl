#!/usr/bin/env python3
"""Test the side-effect-free RM65 joint feedback analyzer."""

from __future__ import annotations

import json

from probe_rm65_joint_feedback import EXPECTED_JOINTS, analyze_samples


def samples() -> list[dict]:
    return [
        {
            "arrival_monotonic_s": index / 100.0,
            "name": EXPECTED_JOINTS.copy(),
            "position": [0.0] * 6,
            "header_stamp_s": index / 100.0,
        }
        for index in range(20)
    ]


def main() -> int:
    valid = analyze_samples(samples(), minimum_samples=20, minimum_rate_hz=20.0)
    wrong_names = samples()
    wrong_names[-1]["name"] = list(reversed(EXPECTED_JOINTS))
    wrong_names_report = analyze_samples(
        wrong_names, minimum_samples=20, minimum_rate_hz=20.0
    )
    nonfinite = samples()
    nonfinite[-1]["position"][2] = float("nan")
    nonfinite_report = analyze_samples(
        nonfinite, minimum_samples=20, minimum_rate_hz=20.0
    )
    passed = (
        valid["status"] == "pass"
        and valid["real_robot_command_sent"] is False
        and valid["publishers_created"] == []
        and wrong_names_report["status"] == "blocked"
        and "joint_names_exact" in wrong_names_report["failed_checks"]
        and nonfinite_report["status"] == "blocked"
        and "positions_finite" in nonfinite_report["failed_checks"]
    )
    print(
        json.dumps(
            {
                "status": "pass" if passed else "fail",
                "valid_feedback": valid,
                "wrong_names_blocked": wrong_names_report["status"] == "blocked",
                "nonfinite_blocked": nonfinite_report["status"] == "blocked",
            },
            indent=2,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
