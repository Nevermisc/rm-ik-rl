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
if [[ "${RM65_ALLOW_LEGACY_DETACHED_PAD_DIAGNOSTIC:-0}" != '1' ]]; then
 echo 'Legacy collision pads are detached from visible fingers. This entrypoint is blocked by default.' >&2
 echo 'Native-gripper geometry must be repaired; only explicit legacy diagnosis may set RM65_ALLOW_LEGACY_DETACHED_PAD_DIAGNOSTIC=1.' >&2
 exit 2
fi
extra+=(--allow-legacy-detached-pad-diagnostic)
recording=(--record-episode-dir "$episode" --record-images --record-stride-steps 12)
if [[ "$mode" == 'free' ]]; then extra+=(--development-free-close-probe)
elif [[ "$mode" == 'ik' ]]; then extra+=(--diagnose-kinematics-only); recording=()
elif [[ "$mode" != 'grasp' ]]; then echo 'mode must be free, ik, or grasp' >&2; exit 2; fi
if [[ "${RM65_VISIBLE_HEADLESS:-0}" == '1' ]]; then echo 'User requires visible experiments; headless refused' >&2; exit 2; fi
source_offset="${RM65_SOURCE_OFFSET_X:--.08}"
object_id="${RM65_OBJECT_ID:-ycb_banana}"
case "$object_id" in
 ycb_banana) manifest=results/household_assets_003.json; object_yaw=0; seed_x=-.04; seed_z=-.053; pad_height=0; preshape=0 ;;
 ycb_large_marker) manifest=results/household_marker_assets_001.json; object_yaw=1.5707963267948966; seed_x=0; seed_z=0; pad_height=.017; preshape=.7 ;;
 *) echo 'This visible controller is only reviewed for banana/marker development' >&2; exit 2 ;;
esac
echo "RM65 SIMULATION ONLY | run=$run_id mode=$mode | object=$object_id | source offset=$source_offset m from historical -0.22128649 m center"
echo 'Force-limited development controller, not pi0.5; all outcomes require the JSON report.'
/home/chengyu/robot-learning/IsaacLab/isaaclab.sh -p scripts/run_pick_place_baseline.py \
 --usd generated/rm65_4c2_wide_pads.usd \
 --urdf /home/chengyu/robot-learning/rm-ik-rl/assets/RM65-B/urdf/RM65-B.urdf \
 --description /home/chengyu/robot-learning/rm-ik-rl/rm65_robot_description.yaml \
 --output "$episode/task_report.json" "${recording[@]}" \
 --development-object "$object_id" --household-manifest "$manifest" --development-object-yaw-rad "$object_yaw" \
 --development-pad-calibration-urdf generated/rm65_4c2_wide_pads.urdf \
 --development-pad-height-offset-m "${RM65_PAD_HEIGHT_OFFSET_M:-$pad_height}" \
 --development-preshape-target-rad "${RM65_PRESHAPE_TARGET_RAD:-$preshape}" \
 --development-gripper-profile force_limited_v1 --development-visible-realtime \
 --development-light-intensity 700 --development-viewer-hold-seconds "${RM65_VIEW_HOLD_SECONDS:-60}" \
 --development-source-support wide_platform --robot-base-z-m .65 \
 --source-offset-x-m "$source_offset" --source-offset-y-m 0 --transfer-joint-1-rad .8 \
 --grasp-world-offset-x-m "$seed_x" --grasp-world-offset-z-m "$seed_z" \
 --grasp-orientation-mode top_down --top-down-yaw-rad 0 --top-down-blend 1 --top-down-ik-multistart 128 \
 --pregrasp-distance-m .09 --natural-source-gravity --enable-moving-gripper-gravity \
 --arm-effort-limit-sim 1000 --arm-stiffness 5000 --arm-damping 300 --gripper-close-target-rad .8 \
 --lift-mode cartesian_vertical --cartesian-lift-height-m .04 --target-support-mode wide_platform \
 --target-collision-enable-stage "${RM65_TARGET_COLLISION_STAGE:-initial}" --place-descent --place-descent-distance-m .13 \
 --place-waypoint-steps 180 --unassisted-release --simulation-seed "${RM65_SIMULATION_SEED:-930301}" \
 --enable_cameras "${extra[@]}"
python3 scripts/check_household_visible_result.py "$episode/task_report.json" --mode "$mode"
