#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
isaaclab_root="${ISAACLAB_ROOT:-$HOME/robot-learning/IsaacLab}"
rm65_root="${RM65_ROOT:-$HOME/robot-learning/rm-ik-rl}"

cd "$project_root"
mkdir -p outputs results

if (($#)); then
  angles=("$@")
else
  angles=(0.6 0.8 1.0)
fi

for angle in "${angles[@]}"; do
  label="${angle/./p}"
  echo "NATURAL_PICK_PLACE_START=$angle"
  "$isaaclab_root/isaaclab.sh" -p scripts/run_pick_place_baseline.py \
    --usd generated/rm65_4c2_wide_pads.usd \
    --urdf "$rm65_root/assets/RM65-B/urdf/RM65-B.urdf" \
    --description "$rm65_root/rm65_robot_description.yaml" \
    --output "outputs/natural_pick_place_${label}.json" \
    --transfer-joint-1-rad "$angle" \
    --pregrasp-distance-m 0.10 \
    --grasp-world-offset-x-m -0.04 \
    --grasp-world-offset-z-m -0.053 \
    --natural-source-gravity \
    --disable-arm-gravity-through-transport \
    --arm-effort-limit-sim 1000 \
    --arm-stiffness 5000 \
    --arm-damping 300 \
    --gripper-effort-limit-sim 200 \
    --gripper-stiffness 2000 \
    --gripper-damping 80 \
    --gripper-close-target-rad 0.80 \
    --lift-mode cartesian_vertical \
    --cartesian-lift-height-m 0.04 \
    --release-separation-assist-m 0.08 \
    --headless \
    > "outputs/natural_pick_place_${label}.log" 2>&1
  echo "NATURAL_PICK_PLACE_DONE=$angle"
done

python3 scripts/summarize_pick_place_natural.py \
  --output results/natural_pick_place_robustness.json
