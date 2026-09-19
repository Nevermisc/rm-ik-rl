#!/usr/bin/env python3
"""Extract finite loss and gradient evidence from an OpenPI training log."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import numpy as np


STEP_PATTERN = re.compile(
    r"Step\s+(?P<step>\d+):\s+grad_norm=(?P<grad>[-+0-9.eE]+),\s+"
    r"loss=(?P<loss>[-+0-9.eE]+),\s+param_norm=(?P<param>[-+0-9.eE]+)"
)
ANSI_PATTERN = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def summarize(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    return {
        "first": float(array[0]),
        "last": float(array[-1]),
        "minimum": float(array.min()),
        "maximum": float(array.max()),
        "mean": float(array.mean()),
        "mean_last_10_logs": float(array[-10:].mean()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    log_path = args.log.expanduser().resolve()
    text = ANSI_PATTERN.sub("", log_path.read_text(encoding="utf-8", errors="replace"))
    records = [
        {
            "step": int(match.group("step")),
            "grad_norm": float(match.group("grad")),
            "loss": float(match.group("loss")),
            "param_norm": float(match.group("param")),
        }
        for match in STEP_PATTERN.finditer(text)
    ]
    if not records:
        raise ValueError(f"no step records found in {log_path}")
    steps = [record["step"] for record in records]
    numeric = [
        value
        for record in records
        for value in (record["grad_norm"], record["loss"], record["param_norm"])
    ]
    unique_increasing = all(right > left for left, right in zip(steps, steps[1:]))
    all_finite = all(math.isfinite(value) for value in numeric)
    report = {
        "status": "pass" if unique_increasing and all_finite else "fail",
        "log": str(log_path),
        "logged_step_count": len(records),
        "first_logged_step": steps[0],
        "last_logged_step": steps[-1],
        "steps_strictly_increasing": unique_increasing,
        "all_metrics_finite": all_finite,
        "loss": summarize([record["loss"] for record in records]),
        "grad_norm": summarize([record["grad_norm"] for record in records]),
        "param_norm": summarize([record["param_norm"] for record in records]),
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "records"}, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
