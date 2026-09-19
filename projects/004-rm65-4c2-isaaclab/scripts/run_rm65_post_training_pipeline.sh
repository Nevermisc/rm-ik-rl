#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
openpi_root="${OPENPI_ROOT:-$HOME/robot-learning/openpi}"
training_pid="${1:?usage: $0 TRAINING_PID}"
training_report="$project_root/results/pi05_rm65_formal_30k.json"
pipeline_log="$project_root/outputs/rm65_post_training_pipeline.log"
sentinel="$project_root/outputs/rm65_post_training_pipeline.status"

cd "$project_root"
mkdir -p outputs results
echo "waiting_for_training_pid=$training_pid" | tee "$sentinel"
while kill -0 "$training_pid" 2>/dev/null; do
  sleep 30
done

if [[ ! -f "$training_report" ]]; then
  echo "failed: training report missing: $training_report" | tee "$sentinel"
  exit 1
fi
checkpoint="$($openpi_root/.venv/bin/python -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d.get("status")=="pass", d; print(d["latest_checkpoint"])' "$training_report")"
if [[ ! -d "$checkpoint" ]]; then
  echo "failed: checkpoint missing: $checkpoint" | tee "$sentinel"
  exit 1
fi

export PYTHONPATH="$project_root:$openpi_root/packages/openpi-client/src${PYTHONPATH:+:$PYTHONPATH}"
validation_episode="$project_root/datasets/rm65_scripted_v1/episode_000000"
norm_stats="$openpi_root/assets/pi05_rm65_lora/local/rm65_sim_train/norm_stats.json"

echo "stage=single_checkpoint_inference checkpoint=$checkpoint" | tee "$sentinel"
"$openpi_root/.venv/bin/python" scripts/validate_rm65_checkpoint.py \
  --checkpoint "$checkpoint" \
  --episode "$validation_episode" \
  --output results/pi05_rm65_formal_checkpoint_inference.json

echo "stage=offline_validation" | tee "$sentinel"
"$openpi_root/.venv/bin/python" scripts/evaluate_rm65_checkpoint_offline.py \
  --checkpoint "$checkpoint" \
  --dataset-root datasets/rm65_scripted_v1 \
  --split validation \
  --frames-per-episode 5 \
  --output results/pi05_rm65_formal_offline_validation.json

echo "stage=simulation_manifest" | tee "$sentinel"
python3 scripts/build_rm65_policy_artifact.py \
  --training-report "$training_report" \
  --norm-stats "$norm_stats" \
  --output results/pi05_rm65_policy_artifact.json
python3 scripts/check_policy_execution_gate.py \
  results/pi05_rm65_policy_artifact.json --target simulation

echo "stage=first_closed_loop" | tee "$sentinel"
bash scripts/run_pi05_rm65_closed_loop.sh \
  "$checkpoint" \
  datasets/rm65_pi05_eval_v1/eval_000 \
  0.65 -0.0075 -0.0075 \
  "pick up the block and place it on the target"

echo "stage=twenty_case_closed_loop_suite" | tee "$sentinel"
python3 scripts/run_pi05_rm65_closed_loop_suite.py \
  --checkpoint "$checkpoint" \
  --plan config/rm65_pi05_evaluation_plan_v1.json \
  --output-root datasets/rm65_pi05_eval_v1 \
  --summary results/rm65_pi05_eval_v1_summary.json

echo "stage=final_manifest" | tee "$sentinel"
python3 scripts/build_rm65_policy_artifact.py \
  --training-report "$training_report" \
  --norm-stats "$norm_stats" \
  --simulation-summary results/rm65_pi05_eval_v1_summary.json \
  --output results/pi05_rm65_policy_artifact.json

echo "pass" | tee "$sentinel"
echo "RM65_POST_TRAINING_PIPELINE=PASS"
