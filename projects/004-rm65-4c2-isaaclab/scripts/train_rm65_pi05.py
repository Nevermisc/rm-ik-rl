#!/usr/bin/env python3
"""Launch OpenPI's JAX trainer with the RM65-B + 4C2 π0.5 LoRA config."""

from __future__ import annotations

import argparse
import dataclasses
import importlib.util
import json
import sys
from pathlib import Path

import openpi


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openpi_extension.rm65_training_config import make_pi05_rm65_lora_config


def load_openpi_trainer():
    openpi_root = Path(openpi.__file__).resolve().parents[2]
    trainer_path = openpi_root / "scripts" / "train.py"
    spec = importlib.util.spec_from_file_location("openpi_jax_train", trainer_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load OpenPI trainer from {trainer_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, openpi_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-id", required=True, help="Choose data explicitly; the old block dataset is not a household default.")
    parser.add_argument("--exp-name", required=True)
    parser.add_argument("--num-train-steps", type=int, default=30_000)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--save-interval", type=int, default=1_000)
    parser.add_argument(
        "--keep-period",
        type=int,
        help=(
            "Permanently retain checkpoints whose step is divisible by this period. "
            "The latest checkpoint is retained independently."
        ),
    )
    parser.add_argument("--log-interval", type=int, default=10)
    parser.add_argument(
        "--initial-params-path",
        default="gs://openpi-assets/checkpoints/pi05_base/params",
        help="Released or trained OpenPI params directory used to initialize this run.",
    )
    parser.add_argument("--warmup-steps", type=int, default=1_000)
    parser.add_argument("--peak-lr", type=float, default=2.5e-5)
    parser.add_argument("--decay-lr", type=float, default=2.5e-6)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.overwrite and args.resume:
        raise ValueError("--overwrite and --resume are mutually exclusive")
    if min(
        args.num_train_steps,
        args.batch_size,
        args.save_interval,
        args.log_interval,
        args.warmup_steps,
    ) < 1:
        raise ValueError("step counts, batch size, and intervals must be positive")
    if not 0.0 < args.decay_lr <= args.peak_lr:
        raise ValueError("learning rates must satisfy 0 < decay-lr <= peak-lr")
    if args.keep_period is not None and args.keep_period < 1:
        raise ValueError("--keep-period must be positive")
    initial_params_path = args.initial_params_path
    if not initial_params_path.startswith("gs://"):
        initial_path = Path(initial_params_path).expanduser().resolve()
        if not initial_path.is_dir():
            raise FileNotFoundError(initial_path)
        initial_params_path = str(initial_path)

    trainer, openpi_root = load_openpi_trainer()
    checkpoint_base = PROJECT_ROOT / "outputs" / "openpi_checkpoints"
    config = make_pi05_rm65_lora_config(
        repo_id=args.repo_id,
        batch_size=args.batch_size,
        num_train_steps=args.num_train_steps,
        initial_params_path=initial_params_path,
        warmup_steps=args.warmup_steps,
        peak_lr=args.peak_lr,
        decay_lr=args.decay_lr,
    )
    config = dataclasses.replace(
        config,
        exp_name=args.exp_name,
        assets_base_dir=str(openpi_root / "assets"),
        checkpoint_base_dir=str(checkpoint_base),
        save_interval=args.save_interval,
        keep_period=args.keep_period,
        log_interval=args.log_interval,
        overwrite=args.overwrite,
        resume=args.resume,
        wandb_enabled=False,
    )
    trainer.main(config)

    numeric_checkpoints = sorted(
        (path for path in config.checkpoint_dir.iterdir() if path.name.isdigit()),
        key=lambda path: int(path.name),
    )
    if not numeric_checkpoints:
        raise RuntimeError(f"training completed without a numeric checkpoint in {config.checkpoint_dir}")
    report = {
        "status": "pass",
        "simulation_only": True,
        "real_robot_command_sent": False,
        "config_name": config.name,
        "repo_id": args.repo_id,
        "exp_name": args.exp_name,
        "batch_size": args.batch_size,
        "num_train_steps": args.num_train_steps,
        "initial_params_path": initial_params_path,
        "warmup_steps": args.warmup_steps,
        "peak_lr": args.peak_lr,
        "decay_lr": args.decay_lr,
        "keep_period": args.keep_period,
        "checkpoint_dir": str(config.checkpoint_dir),
        "latest_checkpoint": str(numeric_checkpoints[-1]),
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
