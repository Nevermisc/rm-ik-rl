#!/usr/bin/env python3
"""Probe deterministic RM65 policy inference without executing any action."""

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

from openpi_client.websocket_client_policy import WebsocketClientPolicy
from openpi_extension.deterministic_policy import (
    POLICY_NOISE_SEED_KEY,
    POLICY_SAMPLING_MODE,
    array_sha256,
    validate_policy_sampling_evidence,
)


ACTION_HORIZON = 10
NOISE_ACTION_DIM = 32
OUTPUT_ACTION_DIM = 7


def read_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.uint8)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", type=Path, required=True)
    parser.add_argument("--frame-index", type=int, default=0)
    parser.add_argument("--policy-noise-seed", type=int, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.policy_noise_seed < 0:
        raise ValueError("--policy-noise-seed must be non-negative")

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

    client = WebsocketClientPolicy(args.host, args.port)
    server_metadata = client.get_server_metadata()
    expected_metadata = {
        "sampling_mode": POLICY_SAMPLING_MODE,
        "deterministic_seed_required": True,
        "model_action_horizon": ACTION_HORIZON,
        "model_action_dim": NOISE_ACTION_DIM,
    }
    mismatches = {
        key: {"expected": value, "actual": server_metadata.get(key)}
        for key, value in expected_metadata.items()
        if server_metadata.get(key) != value
    }
    if mismatches:
        client._ws.close()
        raise RuntimeError(f"policy server metadata mismatch: {mismatches}")

    alternate_seed = args.policy_noise_seed + 1_000_000
    request_seeds = [args.policy_noise_seed, alternate_seed, args.policy_noise_seed]
    records = []
    try:
        for request_index, seed in enumerate(request_seeds):
            request = dict(observation)
            request[POLICY_NOISE_SEED_KEY] = seed
            started = time.perf_counter()
            response = client.infer(request)
            elapsed = time.perf_counter() - started
            sampling = validate_policy_sampling_evidence(
                response.get("policy_sampling"),
                expected_seed=seed,
                action_horizon=ACTION_HORIZON,
                action_dim=NOISE_ACTION_DIM,
            )
            actions = np.asarray(response["actions"], dtype=np.float32)
            if actions.shape != (ACTION_HORIZON, OUTPUT_ACTION_DIM):
                raise ValueError(
                    f"expected actions {(ACTION_HORIZON, OUTPUT_ACTION_DIM)}, got {actions.shape}"
                )
            if not np.isfinite(actions).all():
                raise ValueError("policy returned non-finite actions")
            records.append(
                {
                    "request_index": request_index,
                    **sampling,
                    "action_shape": list(actions.shape),
                    "action_dtype": str(actions.dtype),
                    "action_sha256": array_sha256(actions),
                    "first_action": actions[0].tolist(),
                    "inference_seconds": elapsed,
                }
            )
    finally:
        client._ws.close()

    same_seed_repeated = bool(
        records[0]["noise_sha256"] == records[2]["noise_sha256"]
        and records[0]["action_sha256"] == records[2]["action_sha256"]
    )
    alternate_seed_differs = records[0]["noise_sha256"] != records[1]["noise_sha256"]
    if not same_seed_repeated or not alternate_seed_differs:
        raise RuntimeError("deterministic policy probe failed its repeat/interleave checks")

    report = {
        "status": "pass",
        "validation_kind": "rm65_pi05_deterministic_websocket_probe",
        "simulation_action_executed": False,
        "real_robot_command_sent": False,
        "episode": str(episode),
        "frame_index": index,
        "prompt": metadata["prompt"],
        "policy_noise_seed": args.policy_noise_seed,
        "request_schedule": request_seeds,
        "same_seed_repeated_after_interleave": same_seed_repeated,
        "alternate_seed_noise_differs": alternate_seed_differs,
        "server_metadata": server_metadata,
        "records": records,
    }
    text = json.dumps(report, indent=2) + "\n"
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
