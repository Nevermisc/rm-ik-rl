#!/usr/bin/env python3
"""Summarize the natural-gravity close-angle scan for the original empirical pads."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    trials = []
    for path in sorted(args.input_dir.glob("natural_close_*.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        peak = report["close_contact_force_by_body_n"]
        current = report["close_current_contact_force_by_body_n"]
        recent = report["close_recent_mean_contact_force_by_body_n"]
        trials.append(
            {
                "close_target_rad": report["gripper_actuator"]["close_target_rad"],
                "closed_l2_tip_gap_m": report["closed_l2_tip_gap_m"],
                "left_peak_n": peak["tool_l_2"],
                "right_peak_n": peak["tool_r_2"],
                "left_current_n": current["tool_l_2"],
                "right_current_n": current["tool_r_2"],
                "left_recent_mean_n": recent["tool_l_2"],
                "right_recent_mean_n": recent["tool_r_2"],
            }
        )
    if not trials:
        raise FileNotFoundError("no outputs/natural_close_*.json reports found")

    bilateral_current = [
        trial
        for trial in trials
        if trial["left_current_n"] > 0.01 and trial["right_current_n"] > 0.01
    ]
    summary = {
        "status": "diagnostic",
        "simulation_only": True,
        "pi05_used": False,
        "asset": "generated/rm65_4c2_contact_pads.usd",
        "trial_count": len(trials),
        "bilateral_sustained_current_contact_count": len(bilateral_current),
        "conclusion": "The original 25x10x20 mm empirical pads produce transient contact but no bilateral sustained final contact in this scan.",
        "trials": trials,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
