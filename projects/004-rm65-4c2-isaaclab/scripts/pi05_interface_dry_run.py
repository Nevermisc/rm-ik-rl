#!/usr/bin/env python3
"""Send an RM65 simulation observation to pi0.5, record output, and never execute it."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np
from PIL import Image
import websockets.sync.client as ws


_original_connect = ws.connect


def _connect_without_keepalive(*args, **kwargs):
    kwargs["ping_interval"] = None
    return _original_connect(*args, **kwargs)


ws.connect = _connect_without_keepalive

from openpi_client.websocket_client_policy import WebsocketClientPolicy  # noqa: E402
from openpi_client import image_tools  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observation", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--prompt", default="pick up the red cube")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    observation_path = args.observation.resolve()
    source = json.loads(observation_path.read_text(encoding="utf-8"))
    rm65_joints = np.asarray(source["rm65_joint_position_rad"], dtype=np.float32)
    if rm65_joints.shape != (6,):
        raise ValueError(f"expected six RM65 joints, got {rm65_joints.shape}")
    gripper_joints = np.asarray(source["gripper_joint_position_rad"], dtype=np.float32)
    gripper_scalar = np.array([np.clip(gripper_joints[0] / 0.865, 0.0, 1.0)], dtype=np.float32)

    def image_path(name: str) -> Path:
        recorded = Path(source["images"][name]["path"])
        if recorded.is_absolute() and recorded.exists():
            return recorded
        # Reports use paths relative to observation.json so the project can be
        # mounted at a different location inside the openpi container.
        return observation_path.parent / recorded.name

    external = np.asarray(Image.open(image_path("external")).convert("RGB"))
    wrist = np.asarray(Image.open(image_path("wrist")).convert("RGB"))
    policy_joints = np.concatenate([rm65_joints, np.zeros((1,), dtype=np.float32)])
    request = {
        "observation/exterior_image_1_left": image_tools.resize_with_pad(external, 224, 224),
        "observation/wrist_image_left": image_tools.resize_with_pad(wrist, 224, 224),
        "observation/joint_position": policy_joints,
        "observation/gripper_position": gripper_scalar,
        "prompt": args.prompt,
    }

    client = WebsocketClientPolicy(args.host, args.port)
    start = time.perf_counter()
    actions = np.asarray(client.infer(request)["actions"])
    latency = time.perf_counter() - start
    client._ws.close()
    if actions.ndim != 2 or actions.shape[1] != 8:
        raise ValueError(f"expected pi0.5 DROID actions with shape (T, 8), got {actions.shape}")
    if not np.isfinite(actions).all():
        raise ValueError("pi0.5 returned NaN or Inf")

    report = {
        "status": "pass",
        "executed": False,
        "execution_blocked_reason": [
            "pi05_droid_jointpos outputs seven Franka joint targets, while RM65 has six joints",
            "joint semantics, kinematics, normalization statistics, and gripper calibration do not match",
            "this adapter only validates transport and tensor contracts",
        ],
        "prompt": args.prompt,
        "latency_seconds": latency,
        "policy_input": {
            "joint_position_shape": list(policy_joints.shape),
            "joint_position_source": "RM65 six joints plus one zero-valued virtual joint for dry-run only",
            "gripper_position": gripper_scalar.tolist(),
            "external_image_shape": list(request["observation/exterior_image_1_left"].shape),
            "wrist_image_shape": list(request["observation/wrist_image_left"].shape),
        },
        "policy_output": {
            "shape": list(actions.shape),
            "min": float(actions.min()),
            "max": float(actions.max()),
            "first_action": actions[0].tolist(),
        },
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
