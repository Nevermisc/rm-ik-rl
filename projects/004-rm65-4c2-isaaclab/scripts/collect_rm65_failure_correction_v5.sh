#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mode="${1:-preflight}"
release_backup_manifest="$project_root/results/rm65_pi05_v4_release_backup_manifest.json"
release_source_manifest="$project_root/results/rm65_pi05_v4_release_source_manifest.json"
release_backup_gate="$project_root/results/rm65_pi05_v4_release_backup_gate.json"
plans_validation="$project_root/results/rm65_pi05_failure_correction_v5_plans_validation.json"
collection_gate="$project_root/results/rm65_pi05_failure_correction_v5_collection_gate.json"
plan="$project_root/config/rm65_pi05_failure_correction_v5_expert_plan.json"
dataset="$project_root/datasets/rm65_pi05_failure_correction_v5_expert_v1"

if [[ "$mode" != "preflight" && "$mode" != "first-group" && "$mode" != "run" ]]; then
  echo "usage: $0 [preflight|first-group|run]" >&2
  exit 2
fi

cd "$project_root"
python3 scripts/check_rm65_v4_release_backup_gate.py \
  --backup-manifest "$release_backup_manifest" \
  --source-manifest "$release_source_manifest" \
  --output "$release_backup_gate" >/dev/null
python3 scripts/check_rm65_v5_pipeline_gate.py \
  --stage collection \
  --v4-release-backup-gate "$release_backup_gate" \
  --plans-validation "$plans_validation" \
  --output "$collection_gate" >/dev/null
echo "RM65_FAILURE_CORRECTION_V5_COLLECTION_PREFLIGHT=PASS"

if [[ "$mode" == "preflight" ]]; then
  echo "RM65_FAILURE_CORRECTION_V5_COLLECTION_NOT_STARTED=true"
  exit 0
fi
if pgrep -f '[r]un_expert_collection_plan.py.*rm65_pi05_failure_correction_v5_expert_plan' >/dev/null; then
  echo "ERROR: RM65 v5 collection is already running" >&2
  exit 2
fi
extra_args=()
if [[ "$mode" == "first-group" ]]; then
  extra_args=(--max-cases 4)
fi
exec python3 scripts/run_expert_collection_plan.py \
  --plan "$plan" \
  --dataset-root "$dataset" \
  --split train \
  "${extra_args[@]}"
