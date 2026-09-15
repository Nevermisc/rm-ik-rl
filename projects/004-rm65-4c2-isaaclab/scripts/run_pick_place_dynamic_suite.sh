#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
isaaclab_root="${ISAACLAB_ROOT:-$HOME/robot-learning/IsaacLab}"
rm65_root="${RM65_MODEL_ROOT:-$HOME/robot-learning/rm-ik-rl}"

cd "$project_root"

for trial in "0.02:2" "0.04:4" "0.06:6" "0.10:10"; do
  distance="${trial%%:*}"
  label="${trial##*:}"
  "$isaaclab_root/isaaclab.sh" -p scripts/run_pick_place_baseline.py \
    --usd generated/rm65_4c2_contact_pads.usd \
    --urdf "$rm65_root/assets/RM65-B/urdf/RM65-B.urdf" \
    --description "$rm65_root/rm65_robot_description.yaml" \
    --output "outputs/pick_place_dynamic_${label}cm.json" \
    --pregrasp-distance-m "$distance" \
    --headless
done

python3 scripts/summarize_pick_place_dynamic.py \
  --results outputs \
  --output outputs/pick_place_dynamic_robustness.json
