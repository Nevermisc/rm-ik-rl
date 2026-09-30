#!/usr/bin/env bash
# User-requested visible development session. Never invokes a real robot.
set -euo pipefail
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"
run_id="${1:?run id required}"
mode="${2:-free}"
if [[ ! "$run_id" =~ ^[a-zA-Z0-9_]+$ ]]; then echo 'invalid run id' >&2; exit 2; fi
episode="datasets/rm65_household_visible_${run_id}"
if [[ -e "$episode" ]]; then echo 'fresh episode path required' >&2; exit 2; fi
extra=()
recording=(--record-episode-dir "$episode" --record-images --record-stride-steps 12)
if [[ "$mode" == 'free' ]]; then extra+=(--development-free-close-probe)
elif [[ "$mode" == 'ik' ]]; then extra+=(--diagnose-kinematics-only); recording=()
elif [[ "$mode" != 'grasp' ]]; then echo 'mode must be free, ik, or grasp' >&2; exit 2; fi
if [[ "${RM65_VISIBLE_HEADLESS:-0}" == '1' ]]; then echo 'User requires visible experiments; headless refused' >&2; exit 2; fi
source_offset="${RM65_SOURCE_OFFSET_X:--.08}"
echo "RM65 SIMULATION ONLY | run=$run_id mode=$mode | object=banana | source offset=$source_offset m from historical -0.22128649 m center"
echo 'Force-limited development controller, not pi0.5; all outcomes require the JSON report.'
/home/chengyu/robot-learning/IsaacLab/isaaclab.sh -p scripts/run_pick_place_baseline.py \
 --usd generated/rm65_4c2_wide_pads.usd \
 --urdf /home/chengyu/robot-learning/rm-ik-rl/assets/RM65-B/urdf/RM65-B.urdf \
 --description /home/chengyu/robot-learning/rm-ik-rl/rm65_robot_description.yaml \
 --output "$episode/task_report.json" "${recording[@]}" \
 --development-object ycb_banana --household-manifest results/household_assets_003.json \
 --development-pad-calibration-urdf generated/rm65_4c2_wide_pads.urdf \
 --development-gripper-profile force_limited_v1 --development-visible-realtime \
 --development-light-intensity 700 --development-viewer-hold-seconds "${RM65_VIEW_HOLD_SECONDS:-60}" \
 --development-source-support wide_platform --robot-base-z-m .65 \
 --source-offset-x-m "$source_offset" --source-offset-y-m 0 --transfer-joint-1-rad .8 \
 --grasp-world-offset-x-m -.04 --grasp-world-offset-z-m -.053 \
 --grasp-orientation-mode top_down --top-down-yaw-rad 0 --top-down-blend 1 --top-down-ik-multistart 128 \
 --pregrasp-distance-m .09 --natural-source-gravity --enable-moving-gripper-gravity \
 --arm-effort-limit-sim 1000 --arm-stiffness 5000 --arm-damping 300 --gripper-close-target-rad .8 \
 --lift-mode cartesian_vertical --cartesian-lift-height-m .04 --target-support-mode wide_platform \
 --target-collision-enable-stage "${RM65_TARGET_COLLISION_STAGE:-initial}" --place-descent --place-descent-distance-m .13 \
 --place-waypoint-steps 180 --unassisted-release --simulation-seed "${RM65_SIMULATION_SEED:-930301}" \
 --episode-prompt 'pick up the banana and place it on the target' --enable_cameras "${extra[@]}"
python3 scripts/check_household_visible_result.py "$episode/task_report.json" --mode "$mode"
