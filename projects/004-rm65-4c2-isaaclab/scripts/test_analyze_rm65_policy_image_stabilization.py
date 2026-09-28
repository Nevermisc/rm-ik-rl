#!/usr/bin/env python3
"""Unit checks for exact-policy-image stabilization screening."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

from analyze_rm65_policy_image_stabilization import (
    Candidate,
    apply_candidate,
    build_analysis,
)


def sha256(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def write_episode(root: Path, image: np.ndarray, status: str) -> None:
    episode = root / "case_001"
    observation = episode / "policy_observations"
    observation.mkdir(parents=True)
    views = {}
    hashes = {}
    for view in ("external", "wrist"):
        path = observation / f"chunk_000_{view}.png"
        Image.fromarray(image).save(path)
        digest = sha256(image)
        hashes[f"{view}_image"] = digest
        views[f"{view}_image"] = {
            "path": str(path.relative_to(episode)),
            "shape": list(image.shape),
            "dtype": str(image.dtype),
            "sha256": digest,
        }
    report = {
        "status": status,
        "simulation_only": True,
        "real_robot_command_sent": False,
        "initial_policy_observation": {"chunk_index": 0, **views},
        "deterministic_sampling": {"chunks": [{"observation_sha256": hashes}]},
    }
    (episode / "task_report.json").write_text(json.dumps(report), encoding="utf-8")


def main() -> None:
    base = np.full((9, 9, 3), 100, dtype=np.uint8)
    changed = base.copy()
    changed[4, 4] = 101
    assert np.array_equal(apply_candidate(base, Candidate("identity")), base)
    assert int(apply_candidate(changed, Candidate("q4", quantum=4))[4, 4, 0]) == 100

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        run_a = root / "run_a"
        run_b = root / "run_b"
        run_c = root / "run_c"
        write_episode(run_a, base, "pass")
        write_episode(run_b, changed, "fail")
        write_episode(run_c, base, "pass")
        analysis = build_analysis(
            {"cases": [{"case_id": "case_001"}]},
            [run_a, run_b, run_c],
            lambda image: image,
            candidates=(
                Candidate("identity"),
                Candidate("median3", filter_name="median3"),
            ),
        )
        summaries = {item["name"]: item for item in analysis["candidate_summaries"]}
        assert analysis["case_count"] == 1
        assert analysis["run_count"] == 3
        assert summaries["identity"]["exact_both_view_case_count"] == 0
        assert summaries["median3"]["exact_both_view_case_count"] == 1
        assert analysis["recommended_candidate"] == "median3"
        assert analysis["cases"][0]["statuses"] == ["pass", "fail", "pass"]
    print("policy image stabilization analyzer: 7 checks passed")


if __name__ == "__main__":
    main()
