#!/usr/bin/env bash
set -uo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

dataset_root="${1:-datasets/rm65_scripted_v1}"
mkdir -p "$dataset_root" results

cases=(
  "0.60 -0.015 -0.015"
  "0.60  0.000  0.015"
  "0.60  0.015  0.000"
  "0.80 -0.015  0.015"
  "0.80  0.000  0.000"
  "0.80  0.015 -0.015"
  "1.00 -0.015  0.000"
  "1.00  0.000 -0.015"
  "1.00  0.015  0.015"
)

failed=0
for index in "${!cases[@]}"; do
  read -r angle offset_x offset_y <<< "${cases[$index]}"
  episode_dir=$(printf "%s/episode_%06d" "$dataset_root" "$index")
  echo "RM65_EXPERT_CASE_START=$index angle=$angle x=$offset_x y=$offset_y"
  if ! bash scripts/run_recorded_expert_demo.sh \
    "$episode_dir" "$angle" "$offset_x" "$offset_y"; then
    failed=1
    echo "RM65_EXPERT_CASE_FAIL=$index"
  else
    echo "RM65_EXPERT_CASE_PASS=$index"
  fi
done

python3 scripts/summarize_expert_dataset.py \
  "$dataset_root" \
  --output results/rm65_scripted_dataset_summary.json || failed=1

exit "$failed"
