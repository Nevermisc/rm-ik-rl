#!/usr/bin/env python3
"""Compute OpenPI normalization statistics for the RM65 LeRobot dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import tqdm

import openpi.shared.normalize as normalize
import openpi.training.data_loader as data_loader
import openpi.transforms as transforms


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openpi_extension.rm65_training_config import make_pi05_rm65_lora_config


class RemoveStrings(transforms.DataTransformFn):
    """Drop prompt strings, which are irrelevant to numeric normalization."""

    def __call__(self, sample: dict) -> dict:
        return {
            key: value
            for key, value in sample.items()
            if not np.issubdtype(np.asarray(value).dtype, np.str_)
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-id", default="local/rm65_sim_train")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    config = make_pi05_rm65_lora_config(
        repo_id=args.repo_id,
        batch_size=args.batch_size,
    )
    data_config = config.data.create(config.assets_dirs, config.model)
    dataset = data_loader.create_torch_dataset(
        data_config,
        config.model.action_horizon,
        config.model,
    )
    dataset = data_loader.TransformedDataset(
        dataset,
        [
            *data_config.repack_transforms.inputs,
            *data_config.data_transforms.inputs,
            RemoveStrings(),
        ],
    )
    num_batches = len(dataset) // args.batch_size
    loader = data_loader.TorchDataLoader(
        dataset,
        local_batch_size=args.batch_size,
        num_workers=config.num_workers,
        shuffle=False,
        num_batches=num_batches,
    )

    running = {key: normalize.RunningStats() for key in ("state", "actions")}
    for batch in tqdm.tqdm(loader, total=num_batches, desc="Computing RM65 stats"):
        for key, stats in running.items():
            stats.update(np.asarray(batch[key]))

    norm_stats = {key: stats.get_statistics() for key, stats in running.items()}
    output_dir = config.assets_dirs / data_config.repo_id
    normalize.save(output_dir, norm_stats)
    stats_path = output_dir / "norm_stats.json"
    report = {
        "status": "pass",
        "repo_id": args.repo_id,
        "dataset_frames": len(dataset),
        "processed_frames": num_batches * args.batch_size,
        "batch_size": args.batch_size,
        "output_path": str(stats_path),
        "sha256": hashlib.sha256(stats_path.read_bytes()).hexdigest(),
        "keys": sorted(norm_stats),
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
