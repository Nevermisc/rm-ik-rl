#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
isaaclab_root="${ISAACLAB_ROOT:-$HOME/robot-learning/IsaacLab}"
openpi_root="${OPENPI_ROOT:-$HOME/robot-learning/openpi}"
rm65_root="${RM65_ROOT:-$HOME/robot-learning/rm-ik-rl}"
checkpoint="${1:?usage: $0 CHECKPOINT [EPISODE_DIR] [TRANSFER_ANGLE] [SOURCE_X] [SOURCE_Y] [PROMPT]}"
episode_dir="${2:-datasets/rm65_pi05_eval/episode_000000}"
transfer_angle="${3:-0.8}"
source_offset_x="${4:-0.0}"
source_offset_y="${5:-0.0}"
episode_prompt="${6:-pick up the block and place it on the target}"
policy_port="${POLICY_PORT:-8000}"
server_log="$project_root/outputs/rm65_pi05_policy_server.log"

cd "$project_root"
mkdir -p outputs "$(dirname "$episode_dir")"

if ! command -v ss >/dev/null 2>&1; then
  echo "ERROR: ss is required to check the policy port" >&2
  exit 2
fi
if ss -ltn "sport = :$policy_port" | grep -q LISTEN; then
  echo "ERROR: policy port $policy_port is already in use" >&2
  exit 2
fi

export PYTHONPATH="$project_root:$openpi_root/packages/openpi-client/src${PYTHONPATH:+:$PYTHONPATH}"
# Reserve half of the 16 GB GPU for Isaac Sim. This is the same split that
# passed the earlier Franka + pi0.5 closed-loop evaluation on this workstation.
export XLA_PYTHON_CLIENT_MEM_FRACTION="${XLA_PYTHON_CLIENT_MEM_FRACTION:-0.50}"

"$openpi_root/.venv/bin/python" -u scripts/serve_rm65_policy.py \
  --checkpoint "$checkpoint" \
  --port "$policy_port" \
  >"$server_log" 2>&1 &
server_pid=$!
cleanup() {
  kill "$server_pid" 2>/dev/null || true
  wait "$server_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

for _ in $(seq 1 180); do
  if ! kill -0 "$server_pid" 2>/dev/null; then
    echo "ERROR: policy server stopped during startup" >&2
    tail -n 80 "$server_log" >&2
    exit 1
  fi
  if ss -ltn "sport = :$policy_port" | grep -q LISTEN; then
    break
  fi
  sleep 1
done
if ! ss -ltn "sport = :$policy_port" | grep -q LISTEN; then
  echo "ERROR: policy server did not listen within 180 seconds" >&2
  tail -n 80 "$server_log" >&2
  exit 1
fi

checkpoint_id="$(basename "$(dirname "$checkpoint")")/$(basename "$checkpoint")"
"$isaaclab_root/isaaclab.sh" -p scripts/run_pick_place_baseline.py \
  --usd generated/rm65_4c2_wide_pads.usd \
  --urdf "$rm65_root/assets/RM65-B/urdf/RM65-B.urdf" \
  --description "$rm65_root/rm65_robot_description.yaml" \
  --output "$episode_dir/task_report.json" \
  --record-episode-dir "$episode_dir" \
  --record-stride-steps 12 \
  --record-images \
  --episode-prompt "$episode_prompt" \
  --robot-base-z-m 0.65 \
  --transfer-joint-1-rad "$transfer_angle" \
  --source-offset-x-m "$source_offset_x" \
  --source-offset-y-m "$source_offset_y" \
  --pregrasp-distance-m 0.09 \
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
  --place-descent-distance-m 0.13 \
  --place-waypoint-steps 180 \
  --unassisted-release \
  --pi05-closed-loop \
  --policy-port "$policy_port" \
  --policy-checkpoint-id "$checkpoint_id" \
  --headless \
  --enable_cameras

echo "RM65_PI05_EVALUATION_EPISODE=$episode_dir"
