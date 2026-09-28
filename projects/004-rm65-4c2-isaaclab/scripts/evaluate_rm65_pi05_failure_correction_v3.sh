#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mode="${1:-preflight}"
repo_id="local/rm65_sim_failure_correction_v3_train"
training_report="$project_root/results/pi05_rm65_failure_correction_v3_10k.json"
norm_report="$project_root/results/rm65_pi05_failure_correction_v3_norm_stats.json"
plan="$project_root/config/rm65_pi05_failure_correction_v3_confirmation_20.json"
checkpoint_report="$project_root/results/rm65_pi05_failure_correction_v3_checkpoint_inference.json"
offline_report="$project_root/results/rm65_pi05_failure_correction_v3_offline_validation.json"
repeatability_report="$project_root/results/rm65_pi05_failure_correction_v3_repeatability_20x3.json"

case "$mode" in
  preflight|offline|run1|run2|run3|analyze) ;;
  *)
    echo "usage: $0 [preflight|offline|run1|run2|run3|analyze]" >&2
    exit 2
    ;;
esac

checkpoint="$({ python3 - "$training_report" "$plan" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

training = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
plan = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
if training.get("status") != "pass":
    raise SystemExit("v3 training report is not PASS")
checkpoint = Path(training["latest_checkpoint"])
if not checkpoint.is_dir():
    raise SystemExit(f"v3 checkpoint is missing: {checkpoint}")
checkpoint_id = f"{checkpoint.parent.name}/{checkpoint.name}"
expected = plan.get("frozen_controller_contract", {}).get("checkpoint_id")
if checkpoint_id != expected:
    raise SystemExit(f"checkpoint contract mismatch: expected {expected}, got {checkpoint_id}")
if training.get("repo_id") != plan.get("frozen_controller_contract", {}).get("repo_id"):
    raise SystemExit("training repo id differs from the preregistered controller contract")
print(checkpoint)
PY
} 2>&1)" || {
  echo "$checkpoint" >&2
  exit 1
}

python3 - "$norm_report" "$plan" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

norm = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
plan = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
if norm.get("status") != "pass":
    raise SystemExit("v3 normalization report is not PASS")
if len(plan.get("cases", [])) != 20:
    raise SystemExit("v3 confirmation plan no longer has exactly 20 cases")
if plan.get("gate", {}).get("minimum_success_rate") != 0.9:
    raise SystemExit("v3 confirmation success gate is not 90 percent")
if plan.get("preregistration", {}).get("repeat_count") != 3:
    raise SystemExit("v3 confirmation repeat count is not three")
if plan.get("repeatability_gate", {}).get("minimum_status_consistency_rate") != 0.95:
    raise SystemExit("v3 repeatability consistency gate is not 95 percent")
print("RM65_FAILURE_CORRECTION_V3_EVALUATION_PREFLIGHT=PASS")
PY

if [[ "$mode" == "preflight" ]]; then
  exit 0
fi

cd "$project_root"
if [[ "$mode" == "offline" ]]; then
  PYTHONPATH=. /home/chengyu/robot-learning/openpi/.venv/bin/python \
    scripts/validate_rm65_checkpoint.py \
    --checkpoint "$checkpoint" \
    --episode datasets/rm65_scripted_v1/episode_000000 \
    --repo-id "$repo_id" \
    --output "$checkpoint_report"
  PYTHONPATH=. /home/chengyu/robot-learning/openpi/.venv/bin/python \
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
    --output-root "datasets/rm65_pi05_failure_correction_v3_confirmation_run${repeat_index}" \
    --summary "results/rm65_pi05_failure_correction_v3_confirmation_run${repeat_index}_summary.json"
  exit 0
fi

python3 scripts/analyze_rm65_repeatability_matrix.py \
  --plan "$plan" \
  --run-root datasets/rm65_pi05_failure_correction_v3_confirmation_run1 \
  --run-root datasets/rm65_pi05_failure_correction_v3_confirmation_run2 \
  --run-root datasets/rm65_pi05_failure_correction_v3_confirmation_run3 \
  --output "$repeatability_report"

