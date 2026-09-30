#!/usr/bin/env bash
# Visible finite laboratory development diagnostic. No background scheduler.
set -uo pipefail
cd "$(dirname "$0")/.."
run_id="${1:?fresh run id required}"
protocol="${2:-config/native_household_protocol_v1.json}"
extra_args=()
if [[ "${3:-}" == '--object-collision-precision' ]]; then
  extra_args+=(--object-collision-precision)
elif [[ -n "${3:-}" ]]; then
  echo 'Unsupported diagnostic flag.'
  exit 2
fi
if [[ ! "$run_id" =~ ^native_household_marker_[0-9]{3}$ ]]; then exit 2; fi
log="results/${run_id}.log"
if [[ -e "$log" || -e "outputs/${run_id}" ]]; then
  echo 'Fresh log/output paths required.'
  exit 2
fi
export PYTHONUNBUFFERED=1
/home/chengyu/robot-learning/IsaacLab/isaaclab.sh -p scripts/run_native_household_diagnostic.py \
  --candidate generated/native_surface_source_limits_001 \
  --protocol "$protocol" --asset-manifest results/household_marker_assets_001.json \
  --camera-rig config/camera_rig_native_v1.json --enable_cameras "${extra_args[@]}" \
  --output-dir "outputs/${run_id}" --hold-seconds 45 2>&1 | tee "$log"
result=${PIPESTATUS[0]}
echo "Diagnostic exited ${result}. Read physical evidence and actual RGB; process exit is not grasp success."
echo 'Physics stopped. Press Enter to close this terminal.'
read -r _
exit "$result"
