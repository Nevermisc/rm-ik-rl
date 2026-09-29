#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mode="${1:-preflight}"
backup_manifest="$project_root/results/rm65_pi05_v3_backup_preservation_manifest.json"
source_manifest="$project_root/results/rm65_pi05_v3_source_preservation_manifest.json"
backup_gate="$project_root/results/rm65_pi05_v3_backup_gate.json"
plans_validation="$project_root/results/rm65_pi05_failure_correction_v4_plans_validation.json"
collection_gate="$project_root/results/rm65_pi05_failure_correction_v4_collection_gate.json"
plan="$project_root/config/rm65_pi05_failure_correction_v4_expert_plan.json"
dataset="$project_root/datasets/rm65_pi05_failure_correction_v4_expert_v1"

if [[ "$mode" != "preflight" && "$mode" != "run" ]]; then
  echo "usage: $0 [preflight|run]" >&2
  exit 2
fi

cd "$project_root"
python3 scripts/check_rm65_v3_backup_gate.py \
  --backup-manifest "$backup_manifest" \
  --source-manifest "$source_manifest" \
  --output "$backup_gate" >/dev/null
python3 scripts/check_rm65_v4_pipeline_gate.py \
  --stage collection \
  --backup-gate "$backup_gate" \
  --plans-validation "$plans_validation" \
  --output "$collection_gate" >/dev/null
echo "RM65_FAILURE_CORRECTION_V4_COLLECTION_PREFLIGHT=PASS"

if [[ "$mode" == "preflight" ]]; then
  echo "RM65_FAILURE_CORRECTION_V4_COLLECTION_NOT_STARTED=true"
  exit 0
fi
if pgrep -f '[r]un_expert_collection_plan.py.*rm65_pi05_failure_correction_v4_expert_plan' >/dev/null; then
  echo "ERROR: RM65 v4 collection is already running" >&2
  exit 2
fi
exec python3 scripts/run_expert_collection_plan.py \
  --plan "$plan" \
  --dataset-root "$dataset" \
  --split train
