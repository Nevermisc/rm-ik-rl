#!/usr/bin/env python3
"""Run one recorded RM65 observation through a trained π0.5 checkpoint."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openpi.policies import policy_config
from openpi_extension.action_guard import guard_action_chunk
from openpi_extension.rm65_training_config import make_pi05_rm65_lora_config


def read_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.uint8)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--episode", type=Path, required=True)
    parser.add_argument("--repo-id", default="local/rm65_sim_train")
    parser.add_argument("--frame-index", type=int, default=0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    checkpoint = args.checkpoint.expanduser().resolve()
    episode = args.episode.expanduser().resolve()
    metadata = json.loads((episode / "metadata.json").read_text(encoding="utf-8"))
    with np.load(episode / "episode.npz") as arrays:
        states = arrays["observation_state"].astype(np.float32, copy=True)
    index = args.frame_index
    if not 0 <= index < len(states):
        raise IndexError(f"frame index {index} outside [0, {len(states)})")

    observation = {
        "observation/joint_position": states[index, :6],
        "observation/gripper_position": states[index, 6:7],
        "observation/external_image": read_rgb(
            episode / metadata["image_paths"]["external"][index]
        ),
        "observation/wrist_image": read_rgb(
            episode / metadata["image_paths"]["wrist"][index]
        ),
        "prompt": metadata["prompt"],
    }
    config = make_pi05_rm65_lora_config(repo_id=args.repo_id, batch_size=1)
    start = time.perf_counter()
    policy = policy_config.create_trained_policy(config, checkpoint)
    load_seconds = time.perf_counter() - start
    start = time.perf_counter()
    result = policy.infer(observation)
    inference_seconds = time.perf_counter() - start
    actions = np.asarray(result["actions"], dtype=np.float32)
    if actions.shape != (config.model.action_horizon, 7):
        raise ValueError(f"expected actions {(config.model.action_horizon, 7)}, got {actions.shape}")
    if not np.isfinite(actions).all():
        raise ValueError("checkpoint returned non-finite actions")
    safe_actions, guard = guard_action_chunk(actions, states[index, :6])
    report = {
        "status": "pass",
        "simulation_only": True,
        "real_robot_command_sent": False,
        "checkpoint": str(checkpoint),
        "episode": str(episode),
        "frame_index": index,
        "prompt": metadata["prompt"],
        "load_seconds": load_seconds,
        "inference_seconds": inference_seconds,
        "actions_shape": list(actions.shape),
        "all_actions_finite": True,
        "first_raw_action": actions[0].tolist(),
        "first_guarded_action": safe_actions[0].tolist(),
        "guard": guard,
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
