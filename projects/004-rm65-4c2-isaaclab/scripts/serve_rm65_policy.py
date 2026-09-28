#!/usr/bin/env python3
"""Serve an RM65-specific π0.5 checkpoint over OpenPI's WebSocket protocol."""

from __future__ import annotations

import argparse
import logging
import socket
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openpi.policies import policy_config
from openpi.serving.websocket_policy_server import WebsocketPolicyServer
from openpi_extension.deterministic_policy import (
    DeterministicRequestPolicy,
    POLICY_SAMPLING_MODE,
)
from openpi_extension.rm65_training_config import make_pi05_rm65_lora_config


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--repo-id", default="local/rm65_sim_train")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--default-prompt", default="pick up the block and place it on the target")
    args = parser.parse_args()

    checkpoint = args.checkpoint.expanduser().resolve()
    config = make_pi05_rm65_lora_config(repo_id=args.repo_id, batch_size=1)
    trained_policy = policy_config.create_trained_policy(
        config,
        checkpoint,
        default_prompt=args.default_prompt,
    )
    policy = DeterministicRequestPolicy(
        trained_policy,
        action_horizon=config.model.action_horizon,
        action_dim=config.model.action_dim,
    )
    metadata = {
        "robot": "RM65-B",
        "gripper": "4C2",
        "model": "pi0.5",
        "checkpoint": str(checkpoint),
        "repo_id": args.repo_id,
        "action_semantics": "six absolute joint targets plus normalized gripper target",
        "sampling_mode": POLICY_SAMPLING_MODE,
        "deterministic_seed_required": True,
        "model_action_horizon": config.model.action_horizon,
        "model_action_dim": config.model.action_dim,
    }
    hostname = socket.gethostname()
    logging.info("Creating RM65 policy server (host=%s, listen=%s:%d)", hostname, args.host, args.port)
    WebsocketPolicyServer(
        policy=policy,
        host=args.host,
        port=args.port,
        metadata=metadata,
    ).serve_forever()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, force=True)
    main()
