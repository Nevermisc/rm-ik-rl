#!/usr/bin/env bash
# Starts in the laboratory GNOME terminal. No background scheduling.
set -uo pipefail
cd "$(dirname "$0")/.."
run_id="${1:?fresh run id required}"
protocol="${2:-config/native_contact_protocol_v1.json}"
if [[ ! "$run_id" =~ ^native_contact_[0-9]{3}$ ]]; then exit 2; fi
log="results/${run_id}.log"
if [[ -e "$log" || -e "outputs/${run_id}" ]]; then
  echo 'Fresh log/output paths required.'
  exit 2
fi
export PYTHONUNBUFFERED=1
/home/chengyu/robot-learning/IsaacLab/isaaclab.sh -p scripts/run_native_contact_diagnostic.py \
  --candidate generated/native_surface_source_limits_001 \
  --protocol "$protocol" \
  --output-dir "outputs/${run_id}" --hold-seconds 45 2>&1 | tee "$log"
result=${PIPESTATUS[0]}
echo "Diagnostic process exited ${result}. Read per-size evidence; process exit is not a grasp result."
echo 'Physics stopped. Press Enter to close this terminal.'
read -r _
exit "$result"
