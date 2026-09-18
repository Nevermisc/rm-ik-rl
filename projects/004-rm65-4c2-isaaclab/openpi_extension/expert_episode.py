"""Portable intermediate format for RM65 expert demonstration episodes."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


FORMAT_NAME = "rm65_expert_episode_v1"
JOINT_NAMES = tuple(f"joint_{index}" for index in range(1, 7))


def normalize_gripper(position_rad: float, closed_position_rad: float = 0.865) -> float:
    if closed_position_rad <= 0.0:
        raise ValueError("closed gripper position must be positive")
    return float(np.clip(position_rad / closed_position_rad, 0.0, 1.0))


@dataclass
class EpisodeRecorder:
    """Accumulate synchronized state/action frames and save one episode.

    Each frame represents the observation immediately before applying the
    action target stored at the same index. Images are optional while bringing
    up the low-dimensional recorder, but production training episodes require
    both external and wrist RGB streams.
    """

    output_dir: Path
    prompt: str
    control_hz: float
    metadata: dict[str, Any] = field(default_factory=dict)
    _timestamps: list[float] = field(default_factory=list, init=False)
    _sim_steps: list[int] = field(default_factory=list, init=False)
    _states: list[np.ndarray] = field(default_factory=list, init=False)
    _actions: list[np.ndarray] = field(default_factory=list, init=False)
    _cube_poses: list[np.ndarray] = field(default_factory=list, init=False)
    _phases: list[str] = field(default_factory=list, init=False)
    _external_paths: list[str] = field(default_factory=list, init=False)
    _wrist_paths: list[str] = field(default_factory=list, init=False)
    _images_enabled: bool | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.output_dir = Path(self.output_dir)
        if not self.prompt.strip():
            raise ValueError("episode prompt must not be empty")
        if not np.isfinite(self.control_hz) or self.control_hz <= 0.0:
            raise ValueError("control_hz must be positive and finite")

    def add_frame(
        self,
        *,
        timestamp_s: float,
        sim_step: int,
        phase: str,
        joint_position_rad: np.ndarray,
        gripper_position: float,
        action: np.ndarray,
        cube_pose_wxyz: np.ndarray,
        external_rgb: np.ndarray | None = None,
        wrist_rgb: np.ndarray | None = None,
    ) -> None:
        joints = np.asarray(joint_position_rad, dtype=np.float32)
        action_array = np.asarray(action, dtype=np.float32)
        cube_pose = np.asarray(cube_pose_wxyz, dtype=np.float32)
        if joints.shape != (6,):
            raise ValueError(f"expected six joint positions, got {joints.shape}")
        if action_array.shape != (7,):
            raise ValueError(f"expected seven action values, got {action_array.shape}")
        if cube_pose.shape != (7,):
            raise ValueError(f"expected cube pose [xyz,wxyz], got {cube_pose.shape}")
        if not phase.strip():
            raise ValueError("phase must not be empty")
        if sim_step < 0:
            raise ValueError("sim_step must be non-negative")
        if not 0.0 <= gripper_position <= 1.0:
            raise ValueError("normalized gripper position must be in [0, 1]")
        numeric = np.concatenate(
            [joints, [gripper_position], action_array, cube_pose, [timestamp_s]]
        )
        if not np.isfinite(numeric).all():
            raise ValueError("episode frames must contain only finite numeric values")
        if self._timestamps and timestamp_s <= self._timestamps[-1]:
            raise ValueError("timestamps must be strictly increasing")
        if self._sim_steps and sim_step <= self._sim_steps[-1]:
            raise ValueError("simulation steps must be strictly increasing")
        if (external_rgb is None) != (wrist_rgb is None):
            raise ValueError("external and wrist images must be supplied together")
        frame_has_images = external_rgb is not None
        if self._images_enabled is None:
            self._images_enabled = frame_has_images
        elif self._images_enabled != frame_has_images:
            raise ValueError("all frames in an episode must use the same image streams")

        frame_index = len(self._states)
        external_path = ""
        wrist_path = ""
        if external_rgb is not None:
            from PIL import Image

            external = self._validate_image(external_rgb, "external")
            wrist = self._validate_image(wrist_rgb, "wrist")
            external_path = f"images/external/{frame_index:06d}.png"
            wrist_path = f"images/wrist/{frame_index:06d}.png"
            for relative_path, image in ((external_path, external), (wrist_path, wrist)):
                path = self.output_dir / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                Image.fromarray(image).save(path)

        self._timestamps.append(float(timestamp_s))
        self._sim_steps.append(int(sim_step))
        self._states.append(np.concatenate([joints, [gripper_position]]).astype(np.float32))
        self._actions.append(action_array)
        self._cube_poses.append(cube_pose)
        self._phases.append(phase)
        self._external_paths.append(external_path)
        self._wrist_paths.append(wrist_path)

    @staticmethod
    def _validate_image(image: np.ndarray, name: str) -> np.ndarray:
        array = np.asarray(image)
        if array.ndim != 3 or array.shape[2] != 3:
            raise ValueError(f"{name} image must have shape (H, W, 3), got {array.shape}")
        if array.dtype != np.uint8:
            raise ValueError(f"{name} image must be uint8, got {array.dtype}")
        return array

    def save(self) -> dict[str, Any]:
        if not self._states:
            raise ValueError("cannot save an empty episode")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        phase_names = list(dict.fromkeys(self._phases))
        phase_to_id = {name: index for index, name in enumerate(phase_names)}
        arrays_path = self.output_dir / "episode.npz"
        np.savez_compressed(
            arrays_path,
            timestamp_s=np.asarray(self._timestamps, dtype=np.float64),
            sim_step=np.asarray(self._sim_steps, dtype=np.int64),
            observation_state=np.stack(self._states),
            action=np.stack(self._actions),
            cube_pose_wxyz=np.stack(self._cube_poses),
            phase_id=np.asarray([phase_to_id[item] for item in self._phases], dtype=np.int16),
        )
        has_images = bool(self._images_enabled)
        manifest = {
            "format": FORMAT_NAME,
            "prompt": self.prompt,
            "control_hz": self.control_hz,
            "frame_count": len(self._states),
            "joint_names": list(JOINT_NAMES),
            "observation_state_semantics": [*JOINT_NAMES, "gripper_normalized"],
            "action_semantics": [
                *(f"{name}_absolute_target_rad" for name in JOINT_NAMES),
                "gripper_normalized_target",
            ],
            "cube_pose_semantics": ["x", "y", "z", "qw", "qx", "qy", "qz"],
            "phase_names": phase_names,
            "images_recorded": has_images,
            "image_paths": {
                "external": self._external_paths,
                "wrist": self._wrist_paths,
            },
            "frame_semantics": "observation immediately before applying action at the same index",
            "metadata": self.metadata,
        }
        (self.output_dir / "metadata.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        return manifest


def validate_episode(directory: Path, *, require_images: bool = False) -> dict[str, Any]:
    directory = Path(directory)
    manifest = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    with np.load(directory / "episode.npz") as arrays:
        timestamps = arrays["timestamp_s"]
        sim_steps = arrays["sim_step"]
        states = arrays["observation_state"]
        actions = arrays["action"]
        cube_poses = arrays["cube_pose_wxyz"]
        phase_ids = arrays["phase_id"]

    frame_count = int(manifest["frame_count"])
    errors: list[str] = []
    if manifest.get("format") != FORMAT_NAME:
        errors.append("unexpected episode format")
    expected_shapes = {
        "timestamps": (frame_count,),
        "sim_steps": (frame_count,),
        "states": (frame_count, 7),
        "actions": (frame_count, 7),
        "cube_poses": (frame_count, 7),
        "phase_ids": (frame_count,),
    }
    actual_shapes = {
        "timestamps": timestamps.shape,
        "sim_steps": sim_steps.shape,
        "states": states.shape,
        "actions": actions.shape,
        "cube_poses": cube_poses.shape,
        "phase_ids": phase_ids.shape,
    }
    for name, shape in expected_shapes.items():
        if actual_shapes[name] != shape:
            errors.append(f"{name} shape {actual_shapes[name]} != {shape}")
    if frame_count < 2:
        errors.append("episode must contain at least two frames")
    if not all(np.isfinite(item).all() for item in (timestamps, states, actions, cube_poses)):
        errors.append("episode contains non-finite numeric values")
    if len(timestamps) > 1 and not np.all(np.diff(timestamps) > 0.0):
        errors.append("timestamps are not strictly increasing")
    if len(sim_steps) > 1 and not np.all(np.diff(sim_steps) > 0):
        errors.append("simulation steps are not strictly increasing")
    if states.size and not np.all((states[:, 6] >= 0.0) & (states[:, 6] <= 1.0)):
        errors.append("observed gripper values leave [0, 1]")
    if actions.size and not np.all((actions[:, 6] >= 0.0) & (actions[:, 6] <= 1.0)):
        errors.append("action gripper values leave [0, 1]")
    phase_names = manifest.get("phase_names", [])
    if phase_ids.size and (
        np.min(phase_ids) < 0 or np.max(phase_ids) >= len(phase_names)
    ):
        errors.append("phase ids leave the manifest phase-name range")

    image_paths = manifest.get("image_paths", {})
    external = image_paths.get("external", [])
    wrist = image_paths.get("wrist", [])
    if len(external) != frame_count or len(wrist) != frame_count:
        errors.append("image path lists do not match frame count")
    images_recorded = bool(manifest.get("images_recorded"))
    if require_images and not images_recorded:
        errors.append("images are required but were not recorded")
    if images_recorded:
        missing_images = [
            relative
            for relative in [*external, *wrist]
            if not relative or not (directory / relative).is_file()
        ]
        if missing_images:
            errors.append(f"missing {len(missing_images)} image files")

    return {
        "status": "pass" if not errors else "fail",
        "format": manifest.get("format"),
        "frame_count": frame_count,
        "duration_s": float(timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 0.0,
        "images_recorded": images_recorded,
        "phase_names": manifest.get("phase_names", []),
        "all_finite": not any("non-finite" in item for item in errors),
        "errors": errors,
    }
