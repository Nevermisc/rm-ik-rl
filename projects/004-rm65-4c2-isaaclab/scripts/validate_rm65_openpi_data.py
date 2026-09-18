#!/usr/bin/env python3
"""Load one transformed RM65 batch through OpenPI without starting training."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import jax

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openpi.training import data_loader
from openpi_extension.rm65_training_config import make_pi05_rm65_lora_config


def shape_tree(value):
    return jax.tree.map(
        lambda item: {
            "shape": list(getattr(item, "shape", ())),
            "dtype": str(getattr(item, "dtype", type(item).__name__)),
        },
        value,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-id", default="local/rm65_sim")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    config = make_pi05_rm65_lora_config(repo_id=args.repo_id, batch_size=1)
    loader = data_loader.create_data_loader(
        config,
        shuffle=False,
        num_batches=1,
        skip_norm_stats=True,
    )
    observation, actions = next(iter(loader))
    report = {
        "status": "pass",
        "config_name": config.name,
        "repo_id": args.repo_id,
        "model_type": str(config.model.model_type),
        "action_horizon": config.model.action_horizon,
        "observation": shape_tree(observation),
        "actions": shape_tree(actions),
        "expected_rm65_state_dim": 7,
        "expected_rm65_action_dim_before_padding": 7,
        "normalization_skipped_for_contract_test": True,
    }
    text = json.dumps(report, indent=2, default=str) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
