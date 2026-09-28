#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
openpi_root="${OPENPI_ROOT:-/home/chengyu/robot-learning/openpi}"
mode="${1:-preflight}"
repo_id="local/rm65_sim_failure_correction_v3_train"
initial_params="$project_root/outputs/openpi_checkpoints/pi05_rm65_lora/rm65_policy_window_v2_lora_30k/29999/params"
norm_report="$project_root/results/rm65_pi05_failure_correction_v3_norm_stats.json"
conversion_report="$project_root/results/rm65_pi05_failure_correction_v3_conversion.json"
validation_report="$project_root/results/rm65_pi05_failure_correction_v3_openpi_validation.json"
norm_asset="$openpi_root/assets/pi05_rm65_lora/$repo_id/norm_stats.json"

case "$mode" in
  preflight)
    exp_name="rm65_failure_correction_v3_lora_10k"
    report="$project_root/results/pi05_rm65_failure_correction_v3_10k.json"
    train=false
    resume_args=()
    ;;
  smoke)
    exp_name="rm65_failure_correction_v3_incremental_smoke"
    report="$project_root/results/pi05_rm65_failure_correction_v3_smoke.json"
    train=true
    resume_args=(--overwrite)
    ;;
  start)
    exp_name="rm65_failure_correction_v3_lora_10k"
    report="$project_root/results/pi05_rm65_failure_correction_v3_10k.json"
    train=true
    resume_args=()
    ;;
  resume)
    exp_name="rm65_failure_correction_v3_lora_10k"
    report="$project_root/results/pi05_rm65_failure_correction_v3_10k.json"
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

python3 - "$conversion_report" "$norm_report" "$validation_report" "$norm_asset" "$initial_params" <<'PY'
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

conversion_path, norm_path, validation_path, norm_asset_path, initial_params_path = map(Path, sys.argv[1:])
conversion = json.loads(conversion_path.read_text(encoding="utf-8"))
norm = json.loads(norm_path.read_text(encoding="utf-8"))
validation = json.loads(validation_path.read_text(encoding="utf-8"))
if conversion.get("status") != "pass" or conversion.get("episode_count") != 66:
    raise SystemExit("combined 66-episode conversion report is missing or invalid")
if norm.get("status") != "pass" or validation.get("status") != "pass":
    raise SystemExit("normalization or OpenPI validation report is not PASS")
if not initial_params_path.is_dir():
    raise SystemExit(f"v2 initialization params are missing: {initial_params_path}")
if not norm_asset_path.is_file():
    raise SystemExit(f"normalization asset is missing: {norm_asset_path}")
actual_hash = hashlib.sha256(norm_asset_path.read_bytes()).hexdigest()
if actual_hash != norm.get("sha256"):
    raise SystemExit(f"normalization hash mismatch: expected {norm.get('sha256')}, got {actual_hash}")
print(f"RM65_FAILURE_CORRECTION_V3_TRAINING_PREFLIGHT=PASS sha256={actual_hash}")
PY

if [[ "$train" == false ]]; then
  echo "RM65_FAILURE_CORRECTION_V3_TRAINING_NOT_STARTED=true"
  exit 0
fi

num_steps=10000
save_interval=2000
warmup_steps=500
if [[ "$mode" == "smoke" ]]; then
  num_steps=2
  save_interval=1
  warmup_steps=1
fi

cd "$project_root"
exec "$openpi_root/.venv/bin/python" scripts/train_rm65_pi05.py \
  --repo-id "$repo_id" \
  --exp-name "$exp_name" \
  --num-train-steps "$num_steps" \
  --batch-size 1 \
  --save-interval "$save_interval" \
  --log-interval 1 \
  --initial-params-path "$initial_params" \
  --warmup-steps "$warmup_steps" \
  --peak-lr 5e-6 \
  --decay-lr 1e-6 \
  --report "$report" \
  "${resume_args[@]}"

