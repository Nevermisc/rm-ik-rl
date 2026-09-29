#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
openpi_root="${OPENPI_ROOT:-/home/chengyu/robot-learning/openpi}"
mode="${1:-preflight}"
repo_id="local/rm65_sim_failure_correction_v5_train"
initial_params="$project_root/outputs/openpi_checkpoints/pi05_rm65_lora/rm65_failure_correction_v4_lora_6k/5999/params"
release_backup_manifest="$project_root/results/rm65_pi05_v4_release_backup_manifest.json"
release_source_manifest="$project_root/results/rm65_pi05_v4_release_source_manifest.json"
release_backup_gate="$project_root/results/rm65_pi05_v4_release_backup_gate.json"
v5_collection_backup_gate="$project_root/results/rm65_pi05_v5_collection_backup_gate.json"
plans_validation="$project_root/results/rm65_pi05_failure_correction_v5_plans_validation.json"
v5_summary="$project_root/results/rm65_pi05_failure_correction_v5_expert_v1_summary.json"
render_groups="$project_root/results/rm65_pi05_failure_correction_v5_render_groups.json"
conversion_report="$project_root/results/rm65_pi05_failure_correction_v5_conversion.json"
norm_report="$project_root/results/rm65_pi05_failure_correction_v5_norm_stats.json"
validation_report="$project_root/results/rm65_pi05_failure_correction_v5_openpi_validation.json"
training_gate="$project_root/results/rm65_pi05_failure_correction_v5_training_gate.json"
norm_asset="$openpi_root/assets/pi05_rm65_lora/$repo_id/norm_stats.json"
production_dir="$project_root/outputs/openpi_checkpoints/pi05_rm65_lora/rm65_failure_correction_v5_lora_4k"

case "$mode" in
  preflight)
    exp_name="rm65_failure_correction_v5_lora_4k"
    report="$project_root/results/pi05_rm65_failure_correction_v5_4k.json"
    train=false
    resume_args=()
    ;;
  smoke)
    exp_name="rm65_failure_correction_v5_incremental_smoke"
    report="$project_root/results/pi05_rm65_failure_correction_v5_smoke.json"
    train=true
    resume_args=(--overwrite)
    ;;
  start)
    exp_name="rm65_failure_correction_v5_lora_4k"
    report="$project_root/results/pi05_rm65_failure_correction_v5_4k.json"
    train=true
    resume_args=()
    ;;
  resume)
    exp_name="rm65_failure_correction_v5_lora_4k"
    report="$project_root/results/pi05_rm65_failure_correction_v5_4k.json"
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
  echo "ERROR: frozen v4 initialization params are missing: $initial_params" >&2
  exit 2
fi
if [[ "$mode" == "start" && -e "$production_dir" ]]; then
  echo "ERROR: v5 production output already exists; use resume after inspecting it" >&2
  exit 2
fi
if [[ "$mode" == "resume" && ! -d "$production_dir" ]]; then
  echo "ERROR: v5 production output does not exist; resume is invalid" >&2
  exit 2
fi

cd "$project_root"
python3 scripts/check_rm65_v4_release_backup_gate.py \
  --backup-manifest "$release_backup_manifest" \
  --source-manifest "$release_source_manifest" \
  --output "$release_backup_gate" >/dev/null
python3 scripts/check_rm65_v5_pipeline_gate.py \
  --stage train \
  --v4-release-backup-gate "$release_backup_gate" \
  --plans-validation "$plans_validation" \
  --v5-collection-backup-gate "$v5_collection_backup_gate" \
  --expert-summary "$v5_summary" \
  --render-groups "$render_groups" \
  --conversion "$conversion_report" \
  --norm "$norm_report" \
  --openpi-validation "$validation_report" \
  --norm-asset "$norm_asset" \
  --output "$training_gate" >/dev/null
echo "RM65_FAILURE_CORRECTION_V5_TRAINING_PREFLIGHT=PASS"

if [[ "$train" == false ]]; then
  echo "RM65_FAILURE_CORRECTION_V5_TRAINING_NOT_STARTED=true"
  exit 0
fi

num_steps=4000
save_interval=2000
warmup_steps=200
retention_args=(--keep-period 2000)
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
  --peak-lr 1e-6 \
  --decay-lr 2.5e-7 \
  --report "$report" \
  "${retention_args[@]}" \
  "${resume_args[@]}"
