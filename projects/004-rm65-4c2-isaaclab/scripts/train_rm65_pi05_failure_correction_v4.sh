#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
openpi_root="${OPENPI_ROOT:-/home/chengyu/robot-learning/openpi}"
mode="${1:-preflight}"
repo_id="local/rm65_sim_failure_correction_v4_train"
initial_params="$project_root/outputs/openpi_checkpoints/pi05_rm65_lora/rm65_failure_correction_v3_lora_10k/9999/params"
backup_manifest="$project_root/results/rm65_pi05_v3_backup_preservation_manifest.json"
source_manifest="$project_root/results/rm65_pi05_v3_source_preservation_manifest.json"
backup_gate="$project_root/results/rm65_pi05_v3_backup_gate.json"
v4_collection_backup_gate="$project_root/results/rm65_pi05_v4_collection_backup_gate.json"
plans_validation="$project_root/results/rm65_pi05_failure_correction_v4_plans_validation.json"
v4_summary="$project_root/results/rm65_pi05_failure_correction_v4_expert_v1_summary.json"
render_groups="$project_root/results/rm65_pi05_failure_correction_v4_render_groups.json"
conversion_report="$project_root/results/rm65_pi05_failure_correction_v4_conversion.json"
norm_report="$project_root/results/rm65_pi05_failure_correction_v4_norm_stats.json"
validation_report="$project_root/results/rm65_pi05_failure_correction_v4_openpi_validation.json"
training_gate="$project_root/results/rm65_pi05_failure_correction_v4_training_gate.json"
norm_asset="$openpi_root/assets/pi05_rm65_lora/$repo_id/norm_stats.json"
production_dir="$project_root/outputs/openpi_checkpoints/pi05_rm65_lora/rm65_failure_correction_v4_lora_6k"

case "$mode" in
  preflight)
    exp_name="rm65_failure_correction_v4_lora_6k"
    report="$project_root/results/pi05_rm65_failure_correction_v4_6k.json"
    train=false
    resume_args=()
    ;;
  smoke)
    exp_name="rm65_failure_correction_v4_incremental_smoke"
    report="$project_root/results/pi05_rm65_failure_correction_v4_smoke.json"
    train=true
    resume_args=(--overwrite)
    ;;
  start)
    exp_name="rm65_failure_correction_v4_lora_6k"
    report="$project_root/results/pi05_rm65_failure_correction_v4_6k.json"
    train=true
    resume_args=()
    ;;
  resume)
    exp_name="rm65_failure_correction_v4_lora_6k"
    report="$project_root/results/pi05_rm65_failure_correction_v4_6k.json"
    train=true
    resume_args=(--resume)
    ;;
  *)
    echo "usage: $0 [preflight|smoke|start|resume]" >&2
    exit 2
    ;;
esac

if [[ "$train" == true ]] && pgrep -f '[t]rain_rm65_pi05.py' >/dev/null; then
  echo "ERROR: another RM65 pi0.5 training process is already running" >&2
  exit 2
fi
if [[ ! -d "$initial_params" ]]; then
  echo "ERROR: frozen v3 initialization params are missing: $initial_params" >&2
  exit 2
fi
if [[ "$mode" == "start" && -e "$production_dir" ]]; then
  echo "ERROR: v4 production output already exists; use resume after inspecting it" >&2
  exit 2
fi
if [[ "$mode" == "resume" && ! -d "$production_dir" ]]; then
  echo "ERROR: v4 production output does not exist; resume is invalid" >&2
  exit 2
fi

cd "$project_root"
python3 scripts/check_rm65_v3_backup_gate.py \
  --backup-manifest "$backup_manifest" \
  --source-manifest "$source_manifest" \
  --output "$backup_gate" >/dev/null
python3 scripts/check_rm65_v4_pipeline_gate.py \
  --stage train \
  --backup-gate "$backup_gate" \
  --plans-validation "$plans_validation" \
  --v4-collection-backup-gate "$v4_collection_backup_gate" \
  --expert-summary "$v4_summary" \
  --render-groups "$render_groups" \
  --conversion "$conversion_report" \
  --norm "$norm_report" \
  --openpi-validation "$validation_report" \
  --norm-asset "$norm_asset" \
  --output "$training_gate" >/dev/null
echo "RM65_FAILURE_CORRECTION_V4_TRAINING_PREFLIGHT=PASS"

if [[ "$train" == false ]]; then
  echo "RM65_FAILURE_CORRECTION_V4_TRAINING_NOT_STARTED=true"
  exit 0
fi

num_steps=6000
save_interval=2000
warmup_steps=300
retention_args=(--keep-period 4000)
if [[ "$mode" == "smoke" ]]; then
  num_steps=2
  save_interval=1
  warmup_steps=1
  retention_args=()
fi

exec "$openpi_root/.venv/bin/python" scripts/train_rm65_pi05.py \
  --repo-id "$repo_id" \
  --exp-name "$exp_name" \
  --num-train-steps "$num_steps" \
  --batch-size 1 \
  --save-interval "$save_interval" \
  --log-interval 1 \
  --initial-params-path "$initial_params" \
  --warmup-steps "$warmup_steps" \
  --peak-lr 2e-6 \
  --decay-lr 5e-7 \
  --report "$report" \
  "${retention_args[@]}" \
  "${resume_args[@]}"
