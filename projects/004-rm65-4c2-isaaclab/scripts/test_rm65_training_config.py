#!/usr/bin/env python3
"""Check RM65 incremental-training configuration without starting a trainer."""

from __future__ import annotations

import json

from openpi.training import optimizer as training_optimizer

from openpi_extension.rm65_training_config import make_pi05_rm65_lora_config


def main() -> int:
    params_path = "/tmp/rm65-v2/params"
    config = make_pi05_rm65_lora_config(
        repo_id="local/rm65_v3_train",
        batch_size=1,
        num_train_steps=10_000,
        initial_params_path=params_path,
        warmup_steps=500,
        peak_lr=5e-6,
        decay_lr=1e-6,
    )
    assert config.data.repo_id == "local/rm65_v3_train"
    assert config.num_train_steps == 10_000
    assert config.weight_loader.params_path == params_path
    assert isinstance(config.lr_schedule, training_optimizer.CosineDecaySchedule)
    assert config.lr_schedule.warmup_steps == 500
    assert config.lr_schedule.peak_lr == 5e-6
    assert config.lr_schedule.decay_steps == 10_000
    assert config.lr_schedule.decay_lr == 1e-6
    print(json.dumps({"status": "pass", "checks": 8}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
