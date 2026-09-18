#!/usr/bin/env bash
# Reproduce the 4C2 static-contact and gravity-enabled transport evidence.
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
isaaclab_root="${ISAACLAB_ROOT:-$HOME/robot-learning/IsaacLab}"
runner="$isaaclab_root/isaaclab.sh"
test_script="$project_root/scripts/test_gripper_close_stability.py"
usd="$project_root/generated/rm65_4c2_contact_pads.usd"
results="$project_root/results"

if [[ ! -x "$runner" ]]; then
  echo "Isaac Lab runner not found or not executable: $runner" >&2
  exit 2
fi
if [[ ! -f "$usd" ]]; then
  echo "Contact-pad USD not found: $usd" >&2
  exit 2
fi

run_trial() {
  local output_name="$1"
  shift
  echo "[4C2] Running $output_name"
  "$runner" -p "$test_script" \
    --usd "$usd" \
    --output "$results/$output_name" \
    --headless "$@"
}

# Five static trials: center, lateral +/-2 mm, and tool-axis 8/12 mm.
run_trial gripper_contact_pads_center.json
run_trial contact_pads_offset_neg2mm.json --block-width-axis-offset-m -0.002
run_trial contact_pads_offset_pos2mm.json --block-width-axis-offset-m 0.002
run_trial contact_pads_outward_8mm.json --block-inward-offset-m -0.008
run_trial contact_pads_outward_12mm.json --block-inward-offset-m -0.012

# Three transport trials. Gravity is enabled after bilateral contact by default.
run_trial gripper_contact_transport_offset_neg2mm.json --attempt-lift --block-width-axis-offset-m -0.002
run_trial gripper_contact_transport.json --attempt-lift
run_trial gripper_contact_transport_offset_pos2mm.json --attempt-lift --block-width-axis-offset-m 0.002

python3 "$project_root/scripts/summarize_gripper_contact_pads.py" --results "$results"
python3 "$project_root/scripts/summarize_gripper_transport.py" --results "$results"
echo "[4C2] Static and transport suites completed."
