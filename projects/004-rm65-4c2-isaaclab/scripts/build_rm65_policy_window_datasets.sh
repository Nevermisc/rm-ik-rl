#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
openpi_python="${OPENPI_PYTHON:-$HOME/robot-learning/openpi/.venv/bin/python}"
dataset_root="${1:-$project_root/datasets/rm65_scripted_v1}"
status_file="$project_root/outputs/rm65_policy_window_conversion.status"

cd "$project_root"
export PYTHONPATH="$project_root${PYTHONPATH:+:$PYTHONPATH}"
echo "stage=train" | tee "$status_file"
"$openpi_python" scripts/convert_expert_episodes_to_lerobot.py \
  "$dataset_root" \
  --repo-id local/rm65_sim_policy_train \
  --split train \
  --policy-window

echo "stage=validation" | tee "$status_file"
"$openpi_python" scripts/convert_expert_episodes_to_lerobot.py \
  "$dataset_root" \
  --repo-id local/rm65_sim_policy_validation \
  --split validation \
  --policy-window

echo "pass" | tee "$status_file"
echo "RM65_POLICY_WINDOW_CONVERSION=PASS"
