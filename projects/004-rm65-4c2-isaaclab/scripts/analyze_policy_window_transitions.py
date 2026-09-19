#!/usr/bin/env python3
"""Locate action discontinuities introduced by RM65 policy-window filtering."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.05)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    sys.path.insert(0, str(args.project_root))
    from scripts.convert_expert_episodes_to_lerobot import (  # noqa: PLC0415
        load_episode,
        select_policy_window_indices,
    )

    all_exceedances: list[dict[str, object]] = []
    filtering_exceedances: list[dict[str, object]] = []
    maximum: dict[str, object] | None = None
    maximum_filtering_gap: dict[str, object] | None = None
    for metadata in sorted(args.dataset_root.glob("episode_*/metadata.json")):
        episode = load_episode(metadata.parent)
        selected = select_policy_window_indices(episode)
        actions = np.asarray(episode["actions"], dtype=np.float64)
        phase_ids = np.asarray(episode["phase_ids"], dtype=np.int64)
        phase_names = episode["phase_names"]
        for left, right in zip(selected[:-1], selected[1:], strict=True):
            delta = np.abs(actions[right, :6] - actions[left, :6])
            record = {
                "episode": metadata.parent.name,
                "left_index": int(left),
                "right_index": int(right),
                "source_frame_gap": int(right - left),
                "left_phase": phase_names[int(phase_ids[left])],
                "right_phase": phase_names[int(phase_ids[right])],
                "arm_delta_rad": delta.tolist(),
                "max_arm_delta_rad": float(delta.max()),
                "left_action": actions[left].tolist(),
                "right_action": actions[right].tolist(),
            }
            if maximum is None or record["max_arm_delta_rad"] > maximum["max_arm_delta_rad"]:
                maximum = record
            if right - left > 1 and (
                maximum_filtering_gap is None
                or record["max_arm_delta_rad"] > maximum_filtering_gap["max_arm_delta_rad"]
            ):
                maximum_filtering_gap = record
            if record["max_arm_delta_rad"] > args.threshold:
                all_exceedances.append(record)
                if right - left > 1:
                    filtering_exceedances.append(record)

    report = {
        "status": "pass" if not filtering_exceedances else "filtering_threshold_exceeded",
        "threshold_rad": args.threshold,
        "episodes_checked": len(list(args.dataset_root.glob("episode_*/metadata.json"))),
        "all_transition_exceedance_count": len(all_exceedances),
        "filtering_introduced_exceedance_count": len(filtering_exceedances),
        "maximum_transition": maximum,
        "maximum_filtering_gap_transition": maximum_filtering_gap,
        "filtering_introduced_exceedances": filtering_exceedances,
        "note": (
            "Threshold crossings with source_frame_gap=1 already exist in the raw "
            "trajectory and are not introduced by policy-window filtering."
        ),
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
