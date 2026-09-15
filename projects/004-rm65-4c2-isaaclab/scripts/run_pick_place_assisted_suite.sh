#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
isaaclab_root="${ISAACLAB_ROOT:-$HOME/robot-learning/IsaacLab}"
rm65_root="${RM65_MODEL_ROOT:-$HOME/robot-learning/rm-ik-rl}"

cd "$project_root"

for trial in "0.6:0p6" "0.8:0p8" "1.0:1p0"; do
  angle="${trial%%:*}"
  label="${trial##*:}"
  "$isaaclab_root/isaaclab.sh" -p scripts/run_pick_place_baseline.py \
    --usd generated/rm65_4c2_contact_pads.usd \
    --urdf "$rm65_root/assets/RM65-B/urdf/RM65-B.urdf" \
    --description "$rm65_root/rm65_robot_description.yaml" \
    --output "outputs/pick_place_robust_${label}.json" \
    --transfer-joint-1-rad "$angle" \
    --initialize-at-grasp \
    --headless
done

python3 scripts/summarize_pick_place_assisted.py \
  --results outputs \
  --output outputs/pick_place_assisted_robustness.json
