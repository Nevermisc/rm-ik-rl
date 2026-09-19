#!/usr/bin/env python3
"""Convert successful, image-complete RM65 episodes to OpenPI's LeRobot schema."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openpi_extension.expert_episode import validate_episode


def load_episode(directory: Path) -> dict[str, Any]:
    """Load and validate one successful episode without requiring LeRobot."""

    validation = validate_episode(directory, require_images=True)
    if validation["status"] != "pass":
        raise ValueError(f"invalid episode {directory}: {validation['errors']}")
    manifest = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    if manifest.get("metadata", {}).get("task_success") is not True:
        raise ValueError(f"episode is not marked successful: {directory}")
    with np.load(directory / "episode.npz") as arrays:
        states = arrays["observation_state"].astype(np.float32, copy=True)
        actions = arrays["action"].astype(np.float32, copy=True)
        phase_ids = arrays["phase_id"].astype(np.int64, copy=True)
    return {
        "directory": directory,
        "prompt": manifest["prompt"],
        "fps": float(manifest["control_hz"]),
        "states": states,
        "actions": actions,
        "phase_ids": phase_ids,
        "phase_names": manifest["phase_names"],
        "external_paths": manifest["image_paths"]["external"],
        "wrist_paths": manifest["image_paths"]["wrist"],
        "collection_split": manifest.get("metadata", {}).get("collection_split"),
    }


def select_policy_window_indices(episode: dict[str, Any]) -> np.ndarray:
    """Keep control-relevant motion while reducing ambiguous stationary labels.

    The full portable episode remains unchanged. This optional view retains the
    last two frames of pre-transition holds, the first 15 release-settle frames,
    and every motion frame through release. Retreat and final-settle frames are
    omitted because the closed-loop success detector stops after stable release.
    """

    phase_ids = np.asarray(episode["phase_ids"], dtype=np.int64)
    phase_names = episode["phase_names"]
    phases = np.asarray([phase_names[int(index)] for index in phase_ids], dtype=object)
    motion_mask = np.array(
        [
            phase.startswith("APPROACH_")
            or phase.startswith("PLACE_DESCENT_")
            or phase in {"CLOSE", "LIFT", "TRANSFER", "OPEN"}
            for phase in phases
        ],
        dtype=bool,
    )
    selected = set(np.flatnonzero(motion_mask).tolist())
    for phase in (
        "SOURCE_SETTLE",
        "GRASP_HOLD",
        "CLOSE_HOLD",
        "LIFT_HOLD",
        "TARGET_COLLISION_HOLD",
        "PLACE_HOLD",
    ):
        indices = np.flatnonzero(phases == phase)
        selected.update(indices[-2:].tolist())
    release_indices = np.flatnonzero(phases == "RELEASE_SETTLE")
    selected.update(release_indices[:15].tolist())
    result = np.asarray(sorted(selected), dtype=np.int64)
    if len(result) == 0:
        raise ValueError(f"episode contains no recognized policy phases: {episode['directory']}")
    if phases[result[0]] != "SOURCE_SETTLE":
        raise ValueError("policy window must begin with a SOURCE_SETTLE transition frame")
    if "OPEN" not in phases[result] or "RELEASE_SETTLE" not in phases[result]:
        raise ValueError("policy window must contain OPEN and RELEASE_SETTLE")
    return result


def read_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.uint8)


def discover_episodes(
    dataset_root: Path, *, collection_split: str | None = None
) -> list[dict[str, Any]]:
    directories = sorted(
        path.parent for path in dataset_root.glob("episode_*/metadata.json")
    )
    if not directories:
        raise FileNotFoundError(f"no episode_*/metadata.json found below {dataset_root}")
    episodes = [load_episode(directory) for directory in directories]
    if collection_split is not None:
        episodes = [
            episode
            for episode in episodes
            if episode["collection_split"] == collection_split
        ]
        if not episodes:
            raise ValueError(
                f"no episodes use collection split {collection_split!r}"
            )
    fps_values = {round(item["fps"], 9) for item in episodes}
    if len(fps_values) != 1:
        raise ValueError(f"episodes use different control frequencies: {sorted(fps_values)}")
    first = episodes[0]
    first_external = read_rgb(first["directory"] / first["external_paths"][0])
    first_wrist = read_rgb(first["directory"] / first["wrist_paths"][0])
    for episode in episodes:
        if episode["states"].shape[1:] != (7,) or episode["actions"].shape[1:] != (7,):
            raise ValueError(f"unexpected state/action dimensions in {episode['directory']}")
        if len(episode["external_paths"]) != len(episode["states"]):
            raise ValueError(f"external image count changed in {episode['directory']}")
        if len(episode["wrist_paths"]) != len(episode["states"]):
            raise ValueError(f"wrist image count changed in {episode['directory']}")
        external_shape = read_rgb(episode["directory"] / episode["external_paths"][0]).shape
        wrist_shape = read_rgb(episode["directory"] / episode["wrist_paths"][0]).shape
        if external_shape != first_external.shape or wrist_shape != first_wrist.shape:
            raise ValueError("camera shapes must remain constant across all episodes")
    return episodes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--repo-id", required=True, help="LeRobot repository id, e.g. local/rm65_sim")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--split",
        choices=("train", "validation"),
        help="Convert only the declared collection split.",
    )
    parser.add_argument(
        "--policy-window",
        action="store_true",
        help=(
            "Compress stationary holds and omit post-success retreat/final settle. "
            "Use a new repo id; the source episodes are never modified."
        ),
    )
    args = parser.parse_args()

    episodes = discover_episodes(
        args.dataset_root.expanduser().resolve(), collection_split=args.split
    )
    fps = episodes[0]["fps"]
    rounded_fps = round(fps)
    if not np.isclose(fps, rounded_fps):
        raise ValueError(f"LeRobot conversion requires an integer fps, got {fps}")

    try:
        from lerobot.common.datasets.lerobot_dataset import HF_LEROBOT_HOME, LeRobotDataset
    except ImportError as error:
        raise RuntimeError(
            "LeRobot is unavailable. Run this script in the OpenPI environment with `uv run`."
        ) from error

    output_path = (HF_LEROBOT_HOME / args.repo_id).resolve()
    hf_home = Path(HF_LEROBOT_HOME).resolve()
    if hf_home not in output_path.parents:
        raise ValueError("repo id resolves outside HF_LEROBOT_HOME")
    if output_path.exists():
        if not args.overwrite:
            raise FileExistsError(f"dataset already exists: {output_path}; pass --overwrite to replace it")
        shutil.rmtree(output_path)

    first = episodes[0]
    external_shape = read_rgb(first["directory"] / first["external_paths"][0]).shape
    wrist_shape = read_rgb(first["directory"] / first["wrist_paths"][0]).shape
    dataset = LeRobotDataset.create(
        repo_id=args.repo_id,
        robot_type="rm65_4c2",
        fps=int(rounded_fps),
        features={
            "image": {
                "dtype": "image",
                "shape": external_shape,
                "names": ["height", "width", "channel"],
            },
            "wrist_image": {
                "dtype": "image",
                "shape": wrist_shape,
                "names": ["height", "width", "channel"],
            },
            "joints": {"dtype": "float32", "shape": (6,), "names": ["joints"]},
            "gripper": {"dtype": "float32", "shape": (1,), "names": ["gripper"]},
            "actions": {"dtype": "float32", "shape": (7,), "names": ["actions"]},
        },
        image_writer_threads=10,
        image_writer_processes=5,
    )
    total_frames = 0
    source_frames = 0
    selected_phase_counts: dict[str, int] = {}
    for episode in episodes:
        source_frames += len(episode["states"])
        indices = (
            select_policy_window_indices(episode)
            if args.policy_window
            else np.arange(len(episode["states"]), dtype=np.int64)
        )
        for index in indices:
            index = int(index)
            phase = episode["phase_names"][int(episode["phase_ids"][index])]
            selected_phase_counts[phase] = selected_phase_counts.get(phase, 0) + 1
            dataset.add_frame(
                {
                    "image": read_rgb(episode["directory"] / episode["external_paths"][index]),
                    "wrist_image": read_rgb(episode["directory"] / episode["wrist_paths"][index]),
                    "joints": episode["states"][index, :6],
                    "gripper": episode["states"][index, 6:7],
                    "actions": episode["actions"][index],
                    "task": episode["prompt"],
                }
            )
            total_frames += 1
        dataset.save_episode()

    print(
        json.dumps(
            {
                "status": "pass",
                "repo_id": args.repo_id,
                "output_path": str(output_path),
                "episode_count": len(episodes),
                "frame_count": total_frames,
                "source_frame_count": source_frames,
                "policy_window": args.policy_window,
                "selected_phase_counts": dict(sorted(selected_phase_counts.items())),
                "fps": int(rounded_fps),
                "collection_split": args.split,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
