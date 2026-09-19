#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
openpi_root="${OPENPI_ROOT:-$HOME/robot-learning/openpi}"
training_pid="${1:?usage: $0 TRAINING_PID}"
training_report="${RM65_TRAINING_REPORT:-$project_root/results/pi05_rm65_formal_30k.json}"
repo_id="${RM65_REPO_ID:-local/rm65_sim_train}"
norm_stats="${RM65_NORM_STATS:-$openpi_root/assets/pi05_rm65_lora/$repo_id/norm_stats.json}"
result_prefix="${RM65_RESULT_PREFIX:-pi05_rm65_formal}"
evaluation_root="${RM65_EVALUATION_ROOT:-$project_root/datasets/rm65_pi05_eval_v1}"
evaluation_summary="${RM65_EVALUATION_SUMMARY:-$project_root/results/rm65_pi05_eval_v1_summary.json}"
checkpoint_report="$project_root/results/${result_prefix}_checkpoint_inference.json"
offline_report="$project_root/results/${result_prefix}_offline_validation.json"
artifact_report="$project_root/results/${result_prefix}_policy_artifact.json"
taxonomy_report="$project_root/results/${result_prefix}_failure_taxonomy.json"
sentinel="${RM65_PIPELINE_STATUS:-$project_root/outputs/rm65_post_training_pipeline.status}"
policy_window="${RM65_POLICY_WINDOW:-false}"
first_case_timeout_seconds="${RM65_FIRST_CASE_TIMEOUT_SECONDS:-1200}"

cd "$project_root"
mkdir -p outputs results
current_stage="initialization"
on_error() {
  exit_code=$?
  echo "failed: stage=$current_stage exit_code=$exit_code" | tee "$sentinel"
  exit "$exit_code"
}
trap on_error ERR

if [[ ! "$first_case_timeout_seconds" =~ ^[1-9][0-9]*$ ]]; then
  echo "RM65_FIRST_CASE_TIMEOUT_SECONDS must be a positive integer" >&2
  false
fi
if [[ "$policy_window" != "true" && "$policy_window" != "false" ]]; then
  echo "RM65_POLICY_WINDOW must be true or false" >&2
  false
fi
offline_view_args=()
if [[ "$policy_window" == "true" ]]; then
  offline_view_args=(--policy-window)
fi

current_stage="wait_for_training"
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

current_stage="single_checkpoint_inference"
echo "stage=$current_stage checkpoint=$checkpoint" | tee "$sentinel"
"$openpi_root/.venv/bin/python" scripts/validate_rm65_checkpoint.py \
  --checkpoint "$checkpoint" \
  --episode "$validation_episode" \
  --repo-id "$repo_id" \
  --output "$checkpoint_report"

current_stage="offline_validation"
echo "stage=$current_stage" | tee "$sentinel"
"$openpi_root/.venv/bin/python" scripts/evaluate_rm65_checkpoint_offline.py \
  --checkpoint "$checkpoint" \
  --dataset-root datasets/rm65_scripted_v1 \
  --split validation \
  --repo-id "$repo_id" \
  --frames-per-episode 5 \
  --output "$offline_report" \
  "${offline_view_args[@]}"

current_stage="simulation_manifest"
echo "stage=$current_stage" | tee "$sentinel"
python3 scripts/build_rm65_policy_artifact.py \
  --training-report "$training_report" \
  --norm-stats "$norm_stats" \
  --output "$artifact_report"
python3 scripts/check_policy_execution_gate.py \
  "$artifact_report" --target simulation

current_stage="evaluation_plan_validation"
echo "stage=$current_stage" | tee "$sentinel"
python3 scripts/validate_rm65_evaluation_plan.py \
  --collection-plan config/rm65_expert_collection_plan_v1.json \
  --evaluation-plan config/rm65_pi05_evaluation_plan_v1.json \
  --output results/rm65_pi05_evaluation_plan_validation.json

current_stage="first_closed_loop"
echo "stage=$current_stage timeout_seconds=$first_case_timeout_seconds" | tee "$sentinel"
set +e
timeout --signal=TERM --kill-after=30s "${first_case_timeout_seconds}s" \
  bash scripts/run_pi05_rm65_closed_loop.sh \
  "$checkpoint" \
  "$evaluation_root/eval_000" \
  0.65 -0.0075 -0.0075 \
  "pick up the block and place it on the target"
first_case_exit_code=$?
set -e
echo "stage=$current_stage exit_code=$first_case_exit_code continuing_to_full_suite" | tee "$sentinel"

current_stage="twenty_case_closed_loop_suite"
echo "stage=$current_stage" | tee "$sentinel"
set +e
python3 scripts/run_pi05_rm65_closed_loop_suite.py \
  --checkpoint "$checkpoint" \
  --plan config/rm65_pi05_evaluation_plan_v1.json \
  --output-root "$evaluation_root" \
  --summary "$evaluation_summary"
suite_exit_code=$?
set -e
python3 scripts/analyze_rm65_closed_loop_failures.py \
  --plan config/rm65_pi05_evaluation_plan_v1.json \
  --episode-root "$evaluation_root" \
  --output "$taxonomy_report"
if [[ "$suite_exit_code" -ne 0 ]]; then
  trap - ERR
  echo "failed: stage=$current_stage exit_code=$suite_exit_code" | tee "$sentinel"
  exit "$suite_exit_code"
fi

current_stage="final_manifest"
echo "stage=$current_stage" | tee "$sentinel"
python3 scripts/build_rm65_policy_artifact.py \
  --training-report "$training_report" \
  --norm-stats "$norm_stats" \
  --simulation-summary "$evaluation_summary" \
  --output "$artifact_report"

trap - ERR
echo "pass" | tee "$sentinel"
echo "RM65_POST_TRAINING_PIPELINE=PASS"
