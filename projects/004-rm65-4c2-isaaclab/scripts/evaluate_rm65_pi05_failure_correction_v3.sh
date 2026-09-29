#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
openpi_root="${OPENPI_ROOT:-/home/chengyu/robot-learning/openpi}"
mode="${1:-preflight}"
repo_id="local/rm65_sim_failure_correction_v3_train"
training_report="$project_root/results/pi05_rm65_failure_correction_v3_10k.json"
norm_report="$project_root/results/rm65_pi05_failure_correction_v3_norm_stats.json"
plan="$project_root/config/rm65_pi05_failure_correction_v3_confirmation_20.json"
plan_validation="$project_root/results/rm65_pi05_failure_correction_v3_confirmation_20_validation.json"
norm_asset="$openpi_root/assets/pi05_rm65_lora/$repo_id/norm_stats.json"
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
expected_training = {
    "status": "pass",
    "simulation_only": True,
    "real_robot_command_sent": False,
    "config_name": "pi05_rm65_lora",
    "repo_id": "local/rm65_sim_failure_correction_v3_train",
    "exp_name": "rm65_failure_correction_v3_lora_10k",
    "batch_size": 1,
    "num_train_steps": 10000,
    "warmup_steps": 500,
    "peak_lr": 5e-6,
    "decay_lr": 1e-6,
}
training_mismatches = {
    key: {"expected": expected, "actual": training.get(key)}
    for key, expected in expected_training.items()
    if training.get(key) != expected
}
if training_mismatches:
    raise SystemExit(f"v3 training contract mismatch: {training_mismatches}")
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

python3 - "$norm_report" "$plan" "$plan_validation" "$norm_asset" <<'PY'
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

norm = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
plan = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
plan_validation = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
norm_asset = Path(sys.argv[4]).resolve()
if (
    norm.get("status") != "pass"
    or norm.get("repo_id") != "local/rm65_sim_failure_correction_v3_train"
    or norm.get("processed_frames", 0) <= 0
    or set(norm.get("keys", [])) != {"actions", "state"}
):
    raise SystemExit("v3 normalization report contract is invalid")
if Path(norm.get("output_path", "")).resolve() != norm_asset:
    raise SystemExit("normalization report output path differs from evaluation asset")
if not norm_asset.is_file():
    raise SystemExit(f"normalization asset is missing: {norm_asset}")
actual_norm_hash = hashlib.sha256(norm_asset.read_bytes()).hexdigest()
if actual_norm_hash != norm.get("sha256"):
    raise SystemExit("normalization asset hash differs from the frozen report")
validation_checks = plan_validation.get("checks", {})
if (
    plan_validation.get("status") != "pass"
    or not validation_checks
    or not all(validation_checks.values())
):
    raise SystemExit("v3 confirmation plan validation is missing or invalid")
if plan.get("format") != "rm65_pi05_sim_evaluation_plan_deterministic_v1":
    raise SystemExit("v3 confirmation plan format is invalid")
if len(plan.get("cases", [])) != 20:
    raise SystemExit("v3 confirmation plan no longer has exactly 20 cases")
preregistration = plan.get("preregistration", {})
gate = plan.get("gate", {})
controller = plan.get("frozen_controller_contract", {})
repeatability = plan.get("repeatability_gate", {})
required_contract = {
    "created_before_v3_training": preregistration.get("created_before_v3_training") is True,
    "repeat_count": preregistration.get("repeat_count") == 3,
    "first_run_independent": preregistration.get("first_run_is_independent_success_confirmation") is True,
    "later_runs_not_new_trials": preregistration.get("later_runs_are_repeatability_evidence_not_new_success_trials") is True,
    "normal_failures_not_retried": preregistration.get("normal_model_failures_must_not_be_retried") is True,
    "infrastructure_retry_only": preregistration.get("infrastructure_retries_require_missing_valid_report") is True,
    "minimum_episode_count": gate.get("minimum_episode_count") == 20,
    "minimum_success_rate": gate.get("minimum_success_rate") == 0.9,
    "all_reports_required": gate.get("require_all_planned_reports") is True,
    "checkpoint_id": controller.get("checkpoint_id") == "rm65_failure_correction_v3_lora_10k/9999",
    "repo_id": controller.get("repo_id") == "local/rm65_sim_failure_correction_v3_train",
    "policy_max_action_chunks": controller.get("policy_max_action_chunks") == 120,
    "policy_gripper_open_threshold": controller.get("policy_gripper_open_threshold") == 0.12,
    "actual_gripper_open_threshold": controller.get("actual_gripper_open_threshold") == 0.20,
    "required_release_candidate_chunks": controller.get("required_release_candidate_chunks") == 2,
    "required_reports": repeatability.get("required_reports") == 60,
    "minimum_status_consistency_rate": repeatability.get("minimum_status_consistency_rate") == 0.95,
    "maximum_outcome_flip_cases": repeatability.get("maximum_outcome_flip_cases") == 1,
    "initial_joint_hash_match": repeatability.get("require_initial_joint_hash_match") is True,
    "initial_gripper_hash_match": repeatability.get("require_initial_gripper_hash_match") is True,
    "chunk_zero_noise_hash_match": repeatability.get("require_chunk_zero_noise_hash_match") is True,
}
failed_contract = [name for name, passed in required_contract.items() if not passed]
if failed_contract:
    raise SystemExit(f"v3 confirmation contract drifted: {failed_contract}")
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

