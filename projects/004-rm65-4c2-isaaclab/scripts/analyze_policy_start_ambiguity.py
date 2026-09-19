#!/usr/bin/env python3
"""Quantify hold-versus-move label ambiguity at the RM65 policy start state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np


def summarize_view(
    episode: dict[str, Any], selected: np.ndarray, *, horizon: int, motion_threshold_rad: float
) -> dict[str, Any]:
    phase_ids = np.asarray(episode["phase_ids"], dtype=np.int64)
    names = episode["phase_names"]
    phases = np.asarray([names[int(value)] for value in phase_ids], dtype=object)
    actions = np.asarray(episode["actions"], dtype=np.float64)
    source_positions = np.flatnonzero(phases[selected] == "SOURCE_SETTLE")
    details = []
    for position in source_positions:
        sequence_indices = selected[position : position + horizon]
        sequence = actions[sequence_indices, :6]
        displacement = float(np.max(np.abs(sequence - sequence[0])))
        details.append(
            {
                "source_frame_index": int(selected[position]),
                "selected_sequence_position": int(position),
                "horizon_source_indices": sequence_indices.tolist(),
                "maximum_horizon_arm_displacement_rad": displacement,
                "motion_in_horizon": displacement > motion_threshold_rad,
            }
        )
    moving = sum(item["motion_in_horizon"] for item in details)
    return {
        "source_settle_frame_count": len(details),
        "source_frames_with_motion_in_horizon": moving,
        "motion_horizon_fraction": moving / len(details) if details else 0.0,
        "details": details,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--horizon", type=int, default=10)
    parser.add_argument("--motion-threshold-rad", type=float, default=0.005)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.horizon < 2 or args.motion_threshold_rad <= 0:
        raise ValueError("horizon must be at least two and threshold must be positive")

    project_root = args.project_root.expanduser().resolve()
    sys.path.insert(0, str(project_root))
    from scripts.convert_expert_episodes_to_lerobot import (  # noqa: PLC0415
        load_episode,
        select_policy_window_indices,
    )

    episode_reports = []
    full_source_count = 0
    full_moving_count = 0
    policy_source_count = 0
    policy_moving_count = 0
    for metadata in sorted(args.dataset_root.glob("episode_*/metadata.json")):
        episode = load_episode(metadata.parent)
        full = summarize_view(
            episode,
            np.arange(len(episode["actions"]), dtype=np.int64),
            horizon=args.horizon,
            motion_threshold_rad=args.motion_threshold_rad,
        )
        policy = summarize_view(
            episode,
            select_policy_window_indices(episode),
            horizon=args.horizon,
            motion_threshold_rad=args.motion_threshold_rad,
        )
        full_source_count += full["source_settle_frame_count"]
        full_moving_count += full["source_frames_with_motion_in_horizon"]
        policy_source_count += policy["source_settle_frame_count"]
        policy_moving_count += policy["source_frames_with_motion_in_horizon"]
        episode_reports.append(
            {
                "episode": metadata.parent.name,
                "full_dataset": {key: value for key, value in full.items() if key != "details"},
                "policy_window": {
                    key: value for key, value in policy.items() if key != "details"
                },
            }
        )

    full_fraction = full_moving_count / full_source_count if full_source_count else 0.0
    policy_fraction = policy_moving_count / policy_source_count if policy_source_count else 0.0
    passed = policy_fraction > full_fraction and policy_fraction == 1.0
    report = {
        "status": "pass" if passed else "review",
        "analysis_kind": "policy_start_action_horizon_ambiguity",
        "horizon": args.horizon,
        "motion_threshold_rad": args.motion_threshold_rad,
        "episode_count": len(episode_reports),
        "full_dataset": {
            "source_settle_frame_count": full_source_count,
            "source_frames_with_motion_in_horizon": full_moving_count,
            "motion_horizon_fraction": full_fraction,
        },
        "policy_window": {
            "source_settle_frame_count": policy_source_count,
            "source_frames_with_motion_in_horizon": policy_moving_count,
            "motion_horizon_fraction": policy_fraction,
        },
        "interpretation": (
            "A policy has no explicit phase clock. Repeated near-identical SOURCE_SETTLE "
            "observations with hold-only horizons compete with labels that begin moving. "
            "The policy-window view keeps only transition-adjacent start frames."
        ),
        "episodes": episode_reports,
    }
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "episodes"}, indent=2
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
