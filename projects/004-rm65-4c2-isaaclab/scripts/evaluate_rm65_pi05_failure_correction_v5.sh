#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
openpi_root="${OPENPI_ROOT:-/home/chengyu/robot-learning/openpi}"
mode="${1:-preflight}"
repo_id="local/rm65_sim_failure_correction_v5_train"
training_report="$project_root/results/pi05_rm65_failure_correction_v5_4k.json"
training_gate="$project_root/results/rm65_pi05_failure_correction_v5_training_gate.json"
norm_report="$project_root/results/rm65_pi05_failure_correction_v5_norm_stats.json"
plan="$project_root/config/rm65_pi05_failure_correction_v5_confirmation_20.json"
plans_validation="$project_root/results/rm65_pi05_failure_correction_v5_plans_validation.json"
norm_asset="$openpi_root/assets/pi05_rm65_lora/$repo_id/norm_stats.json"
preflight_report="$project_root/results/rm65_pi05_failure_correction_v5_evaluation_preflight.json"
checkpoint_report="$project_root/results/rm65_pi05_failure_correction_v5_checkpoint_inference.json"
offline_report="$project_root/results/rm65_pi05_failure_correction_v5_offline_validation.json"
repeatability_report="$project_root/results/rm65_pi05_failure_correction_v5_repeatability_20x3.json"

case "$mode" in
  preflight|offline|run1|run2|run3|analyze) ;;
  *)
    echo "usage: $0 [preflight|offline|run1|run2|run3|analyze]" >&2
    exit 2
    ;;
esac

cd "$project_root"
checkpoint="$(python3 scripts/check_rm65_v5_evaluation_preflight.py \
  --training-report "$training_report" \
  --training-gate "$training_gate" \
  --norm-report "$norm_report" \
  --plan "$plan" \
  --plans-validation "$plans_validation" \
  --norm-asset "$norm_asset" \
  --output "$preflight_report")"
echo "RM65_FAILURE_CORRECTION_V5_EVALUATION_PREFLIGHT=PASS"

if [[ "$mode" == "preflight" ]]; then
  exit 0
fi

if [[ "$mode" == "offline" ]]; then
  PYTHONPATH=. "$openpi_root/.venv/bin/python" \
    scripts/validate_rm65_checkpoint.py \
    --checkpoint "$checkpoint" \
    --episode datasets/rm65_scripted_v1/episode_000000 \
    --repo-id "$repo_id" \
    --output "$checkpoint_report"
  PYTHONPATH=. "$openpi_root/.venv/bin/python" \
    scripts/evaluate_rm65_checkpoint_offline.py \
    --checkpoint "$checkpoint" \
    --dataset-root datasets/rm65_scripted_v1 \
    --split validation \
    --repo-id "$repo_id" \
    --frames-per-episode 5 \
    --policy-window \
    --output "$offline_report"
  exit 0
fi

if [[ "$mode" =~ ^run([123])$ ]]; then
  repeat_index="${BASH_REMATCH[1]}"
  python3 scripts/run_pi05_rm65_closed_loop_suite.py \
    --checkpoint "$checkpoint" \
    --repo-id "$repo_id" \
    --plan "$plan" \
    --output-root "datasets/rm65_pi05_failure_correction_v5_confirmation_run${repeat_index}" \
    --summary "results/rm65_pi05_failure_correction_v5_confirmation_run${repeat_index}_summary.json"
  exit 0
fi

python3 scripts/analyze_rm65_repeatability_matrix.py \
  --plan "$plan" \
  --run-root datasets/rm65_pi05_failure_correction_v5_confirmation_run1 \
  --run-root datasets/rm65_pi05_failure_correction_v5_confirmation_run2 \
  --run-root datasets/rm65_pi05_failure_correction_v5_confirmation_run3 \
  --output "$repeatability_report"
