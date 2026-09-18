#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
isaaclab_root="${ISAACLAB_ROOT:-$HOME/robot-learning/IsaacLab}"
rm65_root="${RM65_ROOT:-$HOME/robot-learning/rm-ik-rl}"

cd "$project_root"
mkdir -p outputs

for target in 0.45 0.50 0.55 0.60 0.65 0.70 0.75; do
  echo "GRIPPER_SWEEP_START=$target"
  "$isaaclab_root/isaaclab.sh" -p scripts/run_pick_place_baseline.py \
    --usd generated/rm65_4c2_contact_pads.usd \
    --urdf "$rm65_root/assets/RM65-B/urdf/RM65-B.urdf" \
    --description "$rm65_root/rm65_robot_description.yaml" \
    --output "outputs/natural_close_${target}.json" \
    --pregrasp-distance-m 0.10 \
    --grasp-world-offset-x-m -0.04 \
    --natural-source-gravity \
    --gripper-effort-limit-sim 40 \
    --gripper-stiffness 250 \
    --gripper-damping 25 \
    --gripper-close-target-rad "$target" \
    --diagnose-approach-only \
    --headless \
    > "outputs/natural_close_${target}.log" 2>&1
  echo "GRIPPER_SWEEP_DONE=$target"
done

python3 - <<'PY'
import json
from pathlib import Path

for path in sorted(Path("outputs").glob("natural_close_*.json")):
    report = json.loads(path.read_text())
    current = report["close_current_contact_force_by_body_n"]
    recent = report["close_recent_mean_contact_force_by_body_n"]
    peak = report["close_contact_force_by_body_n"]
    print(
        path.stem.removeprefix("natural_close_"),
        "joint=", round(max(report["closed_gripper_joint_position_rad"]), 6),
        "gap=", round(report["closed_l2_tip_gap_m"], 6),
        "L_peak/current/recent=",
        tuple(round(values["tool_l_2"], 6) for values in (peak, current, recent)),
        "R_peak/current/recent=",
        tuple(round(values["tool_r_2"], 6) for values in (peak, current, recent)),
    )
PY
