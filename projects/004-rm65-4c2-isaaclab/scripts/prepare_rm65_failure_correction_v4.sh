#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
openpi_root="${OPENPI_ROOT:-/home/chengyu/robot-learning/openpi}"
mode="${1:-preflight}"
repo_id="local/rm65_sim_failure_correction_v4_train"
base_dataset="$project_root/datasets/rm65_scripted_v1"
v3_correction_dataset="$project_root/datasets/rm65_pi05_failure_correction_expert_v1"
v4_correction_dataset="$project_root/datasets/rm65_pi05_failure_correction_v4_expert_v1"
v4_plan="$project_root/config/rm65_pi05_failure_correction_v4_expert_plan.json"
v4_summary="$project_root/results/rm65_pi05_failure_correction_v4_expert_v1_summary.json"
render_groups="$project_root/results/rm65_pi05_failure_correction_v4_render_groups.json"
backup_manifest="$project_root/results/rm65_pi05_v3_backup_preservation_manifest.json"
source_manifest="$project_root/results/rm65_pi05_v3_source_preservation_manifest.json"
backup_gate="$project_root/results/rm65_pi05_v3_backup_gate.json"
plans_validation="$project_root/results/rm65_pi05_failure_correction_v4_plans_validation.json"
preparation_gate="$project_root/results/rm65_pi05_failure_correction_v4_preparation_gate.json"
training_gate="$project_root/results/rm65_pi05_failure_correction_v4_training_gate.json"
conversion_report="$project_root/results/rm65_pi05_failure_correction_v4_conversion.json"
norm_report="$project_root/results/rm65_pi05_failure_correction_v4_norm_stats.json"
validation_report="$project_root/results/rm65_pi05_failure_correction_v4_openpi_validation.json"
norm_asset="$openpi_root/assets/pi05_rm65_lora/$repo_id/norm_stats.json"

if [[ "$mode" != "preflight" && "$mode" != "run" ]]; then
  echo "usage: $0 [preflight|run]" >&2
  exit 2
fi

cd "$project_root"
mkdir -p results
python3 scripts/check_rm65_v3_backup_gate.py \
  --backup-manifest "$backup_manifest" \
  --source-manifest "$source_manifest" \
  --output "$backup_gate" >/dev/null
python3 scripts/summarize_expert_dataset.py \
  "$v4_correction_dataset" \
  --plan "$v4_plan" \
  --output "$v4_summary" >/dev/null
python3 scripts/analyze_rm65_v4_render_groups.py \
  "$v4_correction_dataset" \
  --plan "$v4_plan" \
  --output "$render_groups" >/dev/null
python3 scripts/check_rm65_v4_pipeline_gate.py \
  --stage prepare \
  --backup-gate "$backup_gate" \
  --plans-validation "$plans_validation" \
  --expert-summary "$v4_summary" \
  --render-groups "$render_groups" \
  --output "$preparation_gate" >/dev/null
echo "RM65_FAILURE_CORRECTION_V4_PREPARATION_INPUTS=PASS"

if [[ "$mode" == "preflight" ]]; then
  echo "RM65_FAILURE_CORRECTION_V4_CONVERSION_NOT_STARTED=true"
  exit 0
fi

PYTHONPATH=. "$openpi_root/.venv/bin/python" \
  scripts/convert_expert_episodes_to_lerobot.py \
  "$base_dataset" \
  "$v3_correction_dataset" \
  "$v4_correction_dataset" \
  --repo-id "$repo_id" \
  --split train \
  --policy-window \
  --overwrite \
  --report "$conversion_report"

PYTHONPATH=. "$openpi_root/.venv/bin/python" \
  scripts/compute_rm65_norm_stats.py \
  --repo-id "$repo_id" \
  --batch-size 64 \
  --assets-base-dir "$openpi_root/assets" \
  --output "$norm_report"

PYTHONPATH=. "$openpi_root/.venv/bin/python" \
  scripts/validate_rm65_openpi_data.py \
  --repo-id "$repo_id" \
  --output "$validation_report"

python3 scripts/check_rm65_v4_pipeline_gate.py \
  --stage train \
  --backup-gate "$backup_gate" \
  --plans-validation "$plans_validation" \
  --expert-summary "$v4_summary" \
  --render-groups "$render_groups" \
  --conversion "$conversion_report" \
  --norm "$norm_report" \
  --openpi-validation "$validation_report" \
  --norm-asset "$norm_asset" \
  --output "$training_gate" >/dev/null
echo "RM65_FAILURE_CORRECTION_V4_PREPARATION=PASS"
