#!/usr/bin/env python3
"""Summarize RM65 expert state/action ranges and phase coverage by split."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np


def vector_stats(values: np.ndarray) -> dict:
    return {
        "minimum": values.min(axis=0).tolist(),
        "maximum": values.max(axis=0).tolist(),
        "mean": values.mean(axis=0).tolist(),
        "std": values.std(axis=0).tolist(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    dataset_root = args.dataset_root.expanduser().resolve()

    by_split: dict[str, dict] = {}
    first_frames = []
    for episode in sorted(dataset_root.glob("episode_*")):
        metadata_path = episode / "metadata.json"
        arrays_path = episode / "episode.npz"
        if not metadata_path.is_file() or not arrays_path.is_file():
            continue
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        split = metadata.get("metadata", {}).get("collection_split", "unknown")
        with np.load(arrays_path) as arrays:
            states = arrays["observation_state"].astype(np.float64, copy=True)
            actions = arrays["action"].astype(np.float64, copy=True)
            phase_ids = arrays["phase_id"].astype(np.int64, copy=True)
        if states.shape != actions.shape or states.shape[1] != 7:
            raise ValueError(f"unexpected state/action shape in {episode}: {states.shape}/{actions.shape}")
        if not np.isfinite(states).all() or not np.isfinite(actions).all():
            raise ValueError(f"non-finite state/action in {episode}")
        phase_names = metadata["phase_names"]
        phases = [phase_names[int(index)] for index in phase_ids]
        record = by_split.setdefault(
            split,
            {
                "episodes": 0,
                "states": [],
                "actions": [],
                "phase_counts": Counter(),
                "max_abs_action_minus_state_arm": 0.0,
            },
        )
        record["episodes"] += 1
        record["states"].append(states)
        record["actions"].append(actions)
        record["phase_counts"].update(phases)
        record["max_abs_action_minus_state_arm"] = max(
            record["max_abs_action_minus_state_arm"],
            float(np.max(np.abs(actions[:, :6] - states[:, :6]))),
        )
        first_frames.append(
            {
                "episode": episode.name,
                "split": split,
                "phase": phases[0],
                "state": states[0].tolist(),
                "action": actions[0].tolist(),
                "arm_action_minus_state": (actions[0, :6] - states[0, :6]).tolist(),
            }
        )

    if not by_split:
        raise ValueError(f"no complete episodes found below {dataset_root}")
    split_reports = {}
    for split, record in sorted(by_split.items()):
        states = np.concatenate(record.pop("states"), axis=0)
        actions = np.concatenate(record.pop("actions"), axis=0)
        phase_counts = record.pop("phase_counts")
        split_reports[split] = {
            **record,
            "frames": len(states),
            "state": vector_stats(states),
            "action": vector_stats(actions),
            "phase_counts": dict(sorted(phase_counts.items())),
            "all_first_phases_source_settle": all(
                frame["phase"] == "SOURCE_SETTLE"
                for frame in first_frames
                if frame["split"] == split
            ),
        }

    report = {
        "status": "pass",
        "dataset_root": str(dataset_root),
        "state_semantics": [*(f"joint_{index}_rad" for index in range(1, 7)), "gripper_normalized"],
        "action_semantics": [
            *(f"joint_{index}_absolute_target_rad" for index in range(1, 7)),
            "gripper_normalized_target",
        ],
        "splits": split_reports,
        "first_frames": first_frames,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {"status": report["status"], "dataset_root": report["dataset_root"], "splits": split_reports},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
