#!/usr/bin/env python3
"""Fail unless an RM65 pi0.5 task report independently satisfies all criteria."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openpi_extension.closed_loop_report import validate_closed_loop_task_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--checkpoint-id", required=True)
    parser.add_argument("--policy-noise-seed", type=int, required=True)
    args = parser.parse_args()
    if not args.report.is_file():
        raise FileNotFoundError(f"closed-loop task report missing: {args.report}")
    report = json.loads(args.report.read_text(encoding="utf-8"))
    validation = validate_closed_loop_task_report(
        report,
        expected_checkpoint_id=args.checkpoint_id,
        expected_policy_noise_seed=args.policy_noise_seed,
    )
    print(json.dumps(validation, indent=2))
    return 0 if validation["execution_verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
