#!/usr/bin/env python3
"""Compare one recorded frame from two RM65 simulation episodes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


def sha256(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def comparison(first: np.ndarray, second: np.ndarray) -> dict:
    if first.shape != second.shape:
        return {
            "exact_match": False,
            "first_shape": list(first.shape),
            "second_shape": list(second.shape),
        }
    left = np.asarray(first)
    right = np.asarray(second)
    difference = np.abs(left.astype(np.float64) - right.astype(np.float64))
    return {
        "exact_match": bool(np.array_equal(left, right)),
        "shape": list(left.shape),
        "first_dtype": str(left.dtype),
        "second_dtype": str(right.dtype),
        "first_sha256": sha256(left),
        "second_sha256": sha256(right),
        "different_element_count": int(np.count_nonzero(left != right)),
        "maximum_absolute_difference": float(np.max(difference)) if difference.size else 0.0,
        "mean_absolute_difference": float(np.mean(difference)) if difference.size else 0.0,
    }


def read_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.uint8)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--frame-index", type=int, default=0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    first_dir = args.first.expanduser().resolve()
    second_dir = args.second.expanduser().resolve()
    first_metadata = json.loads((first_dir / "metadata.json").read_text(encoding="utf-8"))
    second_metadata = json.loads((second_dir / "metadata.json").read_text(encoding="utf-8"))
    index = args.frame_index

    with np.load(first_dir / "episode.npz") as first_arrays, np.load(
        second_dir / "episode.npz"
    ) as second_arrays:
        arrays = {
            key: comparison(first_arrays[key][index], second_arrays[key][index])
            for key in ("observation_state", "action", "cube_pose_wxyz")
        }

    images = {}
    for camera in ("external", "wrist"):
        first_path = first_dir / first_metadata["image_paths"][camera][index]
        second_path = second_dir / second_metadata["image_paths"][camera][index]
        images[camera] = comparison(read_rgb(first_path), read_rgb(second_path))

    exact = all(item.get("exact_match") is True for item in [*arrays.values(), *images.values()])
    report = {
        "status": "pass" if exact else "different",
        "validation_kind": "rm65_recorded_episode_frame_comparison",
        "simulation_only": True,
        "real_robot_command_sent": False,
        "frame_index": index,
        "arrays": arrays,
        "images": images,
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.output is not None:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
