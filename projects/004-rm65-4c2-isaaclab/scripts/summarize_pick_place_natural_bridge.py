#!/usr/bin/env python3
"""Summarize the natural-gravity contact bridge and its lift boundary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--results", type=Path, default=Path("results"))
parser.add_argument("--output", type=Path, default=Path("results/pick_place_natural_bridge.json"))
args = parser.parse_args()


def load(name: str) -> dict:
    return json.loads((args.results / name).read_text(encoding="utf-8"))


reference = load("pick_place_contact_reference.json")
natural_contact = load("pick_place_natural_contact_xminus4cm.json")
lift_failure = load("pick_place_natural_lift_failure.json")

if min(reference["close_left_finger_contact_force_n"], reference["close_right_finger_contact_force_n"]) <= 0.05:
    raise RuntimeError("assisted contact reference is no longer bilateral")
if not natural_contact["natural_source_gravity"]:
    raise RuntimeError("natural contact evidence no longer uses source gravity")
if min(
    natural_contact["close_left_finger_contact_force_n"],
    natural_contact["close_right_finger_contact_force_n"],
) <= 0.05:
    raise RuntimeError("natural-gravity contact evidence is no longer bilateral")
if lift_failure.get("failure_stage") != "lift" or lift_failure["block_lift_height_m"] > 0.02:
    raise RuntimeError("expected natural-gravity lift failure was not preserved")

summary = {
    "status": "bilateral_contact_pass_lift_fail",
    "simulation_only": True,
    "pi05_used": False,
    "real_robot_command_sent": False,
    "natural_source_gravity": True,
    "source_support": {
        "type": "narrow_strip_development_support",
        "size_m": lift_failure["source_platform_size_m"],
    },
    "contact_reference": {
        "left_force_n": reference["close_left_finger_contact_force_n"],
        "right_force_n": reference["close_right_finger_contact_force_n"],
    },
    "natural_gravity_contact": {
        "grasp_world_offset_x_m": natural_contact["grasp_world_offset_x_m"],
        "left_force_n": natural_contact["close_left_finger_contact_force_n"],
        "right_force_n": natural_contact["close_right_finger_contact_force_n"],
        "contact_bodies": ["tool_l_2", "tool_r_2"],
    },
    "stronger_grip_lift_attempt": {
        "left_force_n": lift_failure["close_left_finger_contact_force_n"],
        "right_force_n": lift_failure["close_right_finger_contact_force_n"],
        "block_cleared_source_support": False,
        "failure_stage": lift_failure["failure_stage"],
    },
    "next_engineering_step": (
        "Calibrate the 4C2 collision pads and grasp geometry against measured hardware dimensions, "
        "then retest sustained contact before any pi0.5 action execution."
    ),
}

args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2))
