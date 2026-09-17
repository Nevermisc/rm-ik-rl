#!/usr/bin/env python3
"""Summarize task success and paired-image health for RM65 expert episodes."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openpi_extension.expert_episode import validate_episode


def image_metrics(directory: Path, paths: list[str]) -> dict:
    sample_indices = np.linspace(0, len(paths) - 1, min(12, len(paths)), dtype=int)
    hashes = []
    red_counts = []
    standard_deviations = []
    shapes = set()
    for index in sample_indices:
        data = (directory / paths[int(index)]).read_bytes()
        hashes.append(hashlib.sha256(data).hexdigest())
        with Image.open(directory / paths[int(index)]) as image:
            array = np.asarray(image.convert("RGB"), dtype=np.uint8)
        shapes.add(array.shape)
        red = (
            (array[..., 0] > 120)
            & (array[..., 0] > 1.25 * array[..., 1])
            & (array[..., 0] > 1.25 * array[..., 2])
        )
        red_counts.append(int(red.sum()))
        standard_deviations.append(float(array.std()))
    unique_ratio = len(set(hashes)) / len(hashes)
    return {
        "sample_count": len(sample_indices),
        "shapes": [list(shape) for shape in sorted(shapes)],
        "unique_exact_image_ratio": unique_ratio,
        "maximum_red_target_pixel_count": max(red_counts),
        "minimum_rgb_std": min(standard_deviations),
        "passed": (
            len(shapes) == 1
            and unique_ratio >= 0.25
            and max(red_counts) > 20
            and min(standard_deviations) > 1.0
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    directories = sorted(path.parent for path in args.dataset_root.glob("episode_*/metadata.json"))
    episodes = []
    for directory in directories:
        validation = validate_episode(directory, require_images=True)
        metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
        task_path = directory / "task_report.json"
        task = json.loads(task_path.read_text(encoding="utf-8")) if task_path.is_file() else {}
        image_paths = metadata.get("image_paths", {})
        external_metrics = (
            image_metrics(directory, image_paths["external"])
            if validation["status"] == "pass"
            else None
        )
        wrist_metrics = (
            image_metrics(directory, image_paths["wrist"])
            if validation["status"] == "pass"
            else None
        )
        passed = bool(
            validation["status"] == "pass"
            and metadata.get("metadata", {}).get("task_success") is True
            and task.get("status") == "pass"
            and task.get("unassisted_full_task_complete") is True
            and external_metrics["passed"]
            and wrist_metrics["passed"]
        )
        episodes.append(
            {
                "episode": directory.name,
                "status": "pass" if passed else "fail",
                "frame_count": validation.get("frame_count"),
                "duration_s": validation.get("duration_s"),
                "transfer_joint_1_rad": metadata.get("metadata", {}).get(
                    "transfer_joint_1_rad"
                ),
                "source_offset_xy_m": metadata.get("metadata", {}).get(
                    "source_offset_xy_m"
                ),
                "episode_validation": validation,
                "task_status": task.get("status", "missing"),
                "unassisted_full_task_complete": task.get(
                    "unassisted_full_task_complete", False
                ),
                "external_image_metrics": external_metrics,
                "wrist_image_metrics": wrist_metrics,
            }
        )

    passed_count = sum(item["status"] == "pass" for item in episodes)
    report = {
        "status": "pass" if episodes and passed_count == len(episodes) else "fail",
        "simulation_only": True,
        "expert": "scripted",
        "pi05_used": False,
        "real_robot_command_sent": False,
        "dataset_root": str(args.dataset_root.resolve()),
        "episode_count": len(episodes),
        "passed_episode_count": passed_count,
        "success_rate": passed_count / len(episodes) if episodes else 0.0,
        "total_frames": sum(item.get("frame_count") or 0 for item in episodes),
        "episodes": episodes,
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
