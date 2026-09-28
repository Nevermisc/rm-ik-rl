#!/usr/bin/env python3
"""Unit tests for exact policy observation repeatability analysis."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

from analyze_rm65_exact_policy_observation_repeatability import array_sha256
from analyze_rm65_exact_policy_observation_repeatability import build_analysis


def write_episode(root: Path, changed: bool) -> None:
    root.mkdir(parents=True)
    initial = np.zeros((4, 6, 3), dtype=np.uint8)
    if changed:
        initial[1, 2, 0] = 1
    observation_dir = root / "policy_observations"
    observation_dir.mkdir()
    views = {}
    hashes = {}
    for view in ("external", "wrist"):
        path = observation_dir / f"chunk_000_{view}.png"
        Image.fromarray(initial).save(path)
        digest = array_sha256(initial)
        views[f"{view}_image"] = {
            "path": str(path.relative_to(root)),
            "shape": list(initial.shape),
            "dtype": str(initial.dtype),
            "sha256": digest,
        }
        hashes[f"{view}_image"] = digest
    physical_state = {}
    for field, size in (
        ("cube_position", 3),
        ("cube_quaternion", 4),
        ("wrist_tool_position", 3),
        ("wrist_tool_quaternion", 4),
        ("wrist_camera_eye", 3),
        ("wrist_camera_forward", 3),
    ):
        value = np.zeros(size, dtype=np.float32)
        if changed and field == "cube_position":
            value[0] = 1e-6
        physical_state[field] = {
            "values": value.tolist(),
            "shape": list(value.shape),
            "dtype": str(value.dtype),
            "sha256": array_sha256(value),
        }
    report = {
        "status": "pass" if not changed else "fail",
        "initial_policy_observation": {"chunk_index": 0, **views},
        "initial_policy_physical_state": physical_state,
        "deterministic_sampling": {
            "chunks": [
                {
                    "noise_sha256": "same-noise",
                    "raw_action_sha256": "action-a" if not changed else "action-b",
                    "observation_sha256": hashes,
                }
            ]
        },
    }
    (root / "task_report.json").write_text(json.dumps(report), encoding="utf-8")
    (root / "metadata.json").write_text(
        json.dumps({"phase_names": ["PI05_CHUNK_000_ACTION_00"]}), encoding="utf-8"
    )
    action = np.zeros((1, 7), dtype=np.float32)
    if changed:
        action[0, 0] = 0.001
    np.savez(root / "episode.npz", phase_id=np.array([0]), action=action)


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        reference = root / "reference"
        candidate = root / "candidate"
        write_episode(reference, changed=False)
        write_episode(candidate, changed=True)
        analysis = build_analysis(reference, candidate)
        assert analysis["status"] == "pass"
        assert analysis["exact_capture_evidence_verified"]
        assert not analysis["outcome_match"]
        assert analysis["chunk_zero_noise_hash_match"]
        assert not analysis["chunk_zero_raw_action_hash_match"]
        assert analysis["images"]["external"]["render_480x640"]["changed_pixel_count"] == 1
        assert analysis["images"]["external"]["render_480x640"]["maximum_absolute_channel_difference"] == 1
        assert not analysis["executed_first_chunk_action_difference"]["exact_match"]
        assert analysis["initial_physical_state_evidence_present"]
        assert not analysis["initial_physical_state"]["all_hashes_match"]
        assert not analysis["initial_physical_state"]["fields"]["cube_position"][
            "hash_match"
        ]
        assert analysis["initial_physical_state"]["fields"]["cube_quaternion"][
            "hash_match"
        ]

    print(json.dumps({"status": "pass", "checks": 12}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
