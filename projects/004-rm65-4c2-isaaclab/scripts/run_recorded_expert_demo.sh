#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
isaaclab_root="${ISAACLAB_ROOT:-$HOME/robot-learning/IsaacLab}"
rm65_root="${RM65_ROOT:-$HOME/robot-learning/rm-ik-rl}"
episode_dir="${1:-datasets/rm65_scripted_v1/episode_000000}"
transfer_angle="${2:-0.8}"

cd "$project_root"
mkdir -p outputs "$(dirname "$episode_dir")"

"$isaaclab_root/isaaclab.sh" -p scripts/run_pick_place_baseline.py \
  --usd generated/rm65_4c2_wide_pads.usd \
  --urdf "$rm65_root/assets/RM65-B/urdf/RM65-B.urdf" \
  --description "$rm65_root/rm65_robot_description.yaml" \
  --output outputs/recorded_expert_demo.json \
  --record-episode-dir "$episode_dir" \
  --record-stride-steps 12 \
  --record-images \
  --episode-prompt "pick up the block and place it on the target" \
  --robot-base-z-m 0.65 \
  --transfer-joint-1-rad "$transfer_angle" \
  --pregrasp-distance-m 0.10 \
  --grasp-world-offset-x-m -0.04 \
  --grasp-world-offset-z-m -0.053 \
  --grasp-orientation-mode top_down \
  --top-down-yaw-rad 0.0 \
  --top-down-tilt-rad 0.0 \
  --top-down-blend 1.0 \
  --top-down-ik-multistart 128 \
  --natural-source-gravity \
  --enable-moving-gripper-gravity \
  --arm-effort-limit-sim 1000 \
  --arm-stiffness 5000 \
  --arm-damping 300 \
  --gripper-effort-limit-sim 200 \
  --gripper-stiffness 2000 \
  --gripper-damping 80 \
  --gripper-close-target-rad 0.80 \
  --lift-mode cartesian_vertical \
  --cartesian-lift-height-m 0.04 \
  --target-support-mode wide_platform \
  --target-collision-enable-stage after_transfer \
  --place-descent \
  --place-descent-distance-m 0.12 \
  --place-waypoint-steps 60 \
  --unassisted-release \
  --headless \
  --enable_cameras

python3 scripts/validate_expert_episode.py "$episode_dir" --require-images
echo "RM65_RECORDED_EXPERT_EPISODE=$episode_dir"
