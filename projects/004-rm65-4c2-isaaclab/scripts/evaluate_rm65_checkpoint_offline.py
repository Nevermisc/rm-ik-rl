#!/usr/bin/env python3
"""Evaluate one RM65 pi0.5 checkpoint on held-out scripted episodes.

This is an offline imitation check. It measures action error and safety-guard
activity, but it never sends an action to Isaac Sim or to a real robot.
"""

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
from convert_expert_episodes_to_lerobot import select_policy_window_indices


def read_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.uint8)


def select_frames(frame_count: int, horizon: int, count: int) -> list[int]:
    last_start = frame_count - horizon
    if last_start < 0:
        raise ValueError(f"episode has {frame_count} frames, shorter than horizon {horizon}")
    return sorted(set(np.linspace(0, last_start, count, dtype=np.int64).tolist()))


def percentile(values: list[float], q: float) -> float:
    return float(np.percentile(np.asarray(values, dtype=np.float64), q))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--split", default="validation")
    parser.add_argument("--repo-id", default="local/rm65_sim_train")
    parser.add_argument("--frames-per-episode", type=int, default=5)
    parser.add_argument(
        "--policy-window",
        action="store_true",
        help="Evaluate horizons over the same filtered frame sequence used by v2 training.",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.frames_per_episode < 1:
        raise ValueError("--frames-per-episode must be positive")

    checkpoint = args.checkpoint.expanduser().resolve()
    dataset_root = args.dataset_root.expanduser().resolve()
    episodes: list[tuple[Path, dict]] = []
    for episode in sorted(dataset_root.glob("episode_*")):
        metadata_path = episode / "metadata.json"
        if not metadata_path.is_file():
            continue
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("metadata", {}).get("collection_split") == args.split:
            episodes.append((episode, metadata))
    if not episodes:
        raise ValueError(f"no episodes with split={args.split!r} below {dataset_root}")

    config = make_pi05_rm65_lora_config(repo_id=args.repo_id, batch_size=1)
    started = time.perf_counter()
    policy = policy_config.create_trained_policy(config, checkpoint)
    load_seconds = time.perf_counter() - started

    samples = []
    inference_seconds = []
    horizon_arm_abs_errors = []
    horizon_gripper_abs_errors = []
    first_arm_l2_errors = []
    first_gripper_abs_errors = []
    guard_joint_limit_clamps = 0
    guard_joint_step_clamps = 0
    guard_gripper_clamps = 0

    for episode, metadata in episodes:
        with np.load(episode / "episode.npz") as arrays:
            states = arrays["observation_state"].astype(np.float32, copy=True)
            expert_actions = arrays["action"].astype(np.float32, copy=True)
            phase_ids = arrays["phase_id"].astype(np.int64, copy=True)
        phase_names = metadata["phase_names"]
        selected_indices = (
            select_policy_window_indices(
                {
                    "directory": episode,
                    "phase_ids": phase_ids,
                    "phase_names": phase_names,
                }
            )
            if args.policy_window
            else np.arange(len(states), dtype=np.int64)
        )
        selected_positions = select_frames(
            len(selected_indices), config.model.action_horizon, args.frames_per_episode
        )
        for selected_position in selected_positions:
            index = int(selected_indices[selected_position])
            action_indices = selected_indices[
                selected_position : selected_position + config.model.action_horizon
            ]
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
            started = time.perf_counter()
            predicted = np.asarray(policy.infer(observation)["actions"], dtype=np.float32)
            elapsed = time.perf_counter() - started
            expected_shape = (config.model.action_horizon, 7)
            if predicted.shape != expected_shape:
                raise ValueError(f"expected policy actions {expected_shape}, got {predicted.shape}")
            if not np.isfinite(predicted).all():
                raise ValueError(f"non-finite action at {episode.name} frame {index}")

            expert = expert_actions[action_indices]
            guarded, guard = guard_action_chunk(predicted, states[index, :6])
            arm_abs = np.abs(predicted[:, :6] - expert[:, :6])
            gripper_abs = np.abs(predicted[:, 6] - expert[:, 6])
            first_arm_l2 = float(np.linalg.norm(predicted[0, :6] - expert[0, :6]))
            first_gripper_abs = float(abs(predicted[0, 6] - expert[0, 6]))
            inference_seconds.append(elapsed)
            horizon_arm_abs_errors.extend(arm_abs.ravel().tolist())
            horizon_gripper_abs_errors.extend(gripper_abs.tolist())
            first_arm_l2_errors.append(first_arm_l2)
            first_gripper_abs_errors.append(first_gripper_abs)
            guard_joint_limit_clamps += guard["joint_limit_clamp_count"]
            guard_joint_step_clamps += guard["joint_step_clamp_count"]
            guard_gripper_clamps += guard["gripper_clamp_count"]
            samples.append(
                {
                    "episode": episode.name,
                    "case_id": metadata.get("metadata", {}).get("collection_case_id"),
                    "frame_index": index,
                    "policy_window_position": selected_position if args.policy_window else None,
                    "expert_action_frame_indices": action_indices.tolist(),
                    "phase": phase_names[int(phase_ids[index])],
                    "inference_seconds": elapsed,
                    "first_arm_l2_error_rad": first_arm_l2,
                    "first_gripper_abs_error": first_gripper_abs,
                    "horizon_arm_mae_rad": float(np.mean(arm_abs)),
                    "horizon_gripper_mae": float(np.mean(gripper_abs)),
                    "guard": guard,
                    "first_predicted_action": predicted[0].tolist(),
                    "first_guarded_action": guarded[0].tolist(),
                    "first_expert_action": expert[0].tolist(),
                }
            )

    report = {
        "status": "pass",
        "evaluation_kind": "offline_held_out_imitation",
        "simulation_action_executed": False,
        "real_robot_command_sent": False,
        "task_success_claimed": False,
        "checkpoint": str(checkpoint),
        "dataset_root": str(dataset_root),
        "split": args.split,
        "episode_count": len(episodes),
        "sample_count": len(samples),
        "frames_per_episode": args.frames_per_episode,
        "policy_window": args.policy_window,
        "load_seconds": load_seconds,
        "inference_seconds": {
            "first": inference_seconds[0],
            "mean": float(np.mean(inference_seconds)),
            "p95": percentile(inference_seconds, 95),
            "maximum": float(np.max(inference_seconds)),
        },
        "action_error": {
            "horizon_arm_mae_rad": float(np.mean(horizon_arm_abs_errors)),
            "horizon_arm_p95_abs_error_rad": percentile(horizon_arm_abs_errors, 95),
            "horizon_gripper_mae": float(np.mean(horizon_gripper_abs_errors)),
            "horizon_gripper_p95_abs_error": percentile(horizon_gripper_abs_errors, 95),
            "first_action_arm_mean_l2_error_rad": float(np.mean(first_arm_l2_errors)),
            "first_action_arm_max_l2_error_rad": float(np.max(first_arm_l2_errors)),
            "first_action_gripper_mae": float(np.mean(first_gripper_abs_errors)),
        },
        "guard_totals": {
            "joint_limit_clamp_count": guard_joint_limit_clamps,
            "joint_step_clamp_count": guard_joint_step_clamps,
            "gripper_clamp_count": guard_gripper_clamps,
        },
        "interpretation": (
            "PASS means all held-out observations produced finite, shape-correct actions. "
            "Offline action error does not prove closed-loop task success."
        ),
        "samples": samples,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "samples"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
