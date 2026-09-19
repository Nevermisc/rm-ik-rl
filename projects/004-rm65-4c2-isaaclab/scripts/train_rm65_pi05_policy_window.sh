#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
openpi_root="${OPENPI_ROOT:-$HOME/robot-learning/openpi}"
mode="${1:-start}"
repo_id="local/rm65_sim_policy_train"
exp_name="rm65_policy_window_v2_lora_30k"
report="$project_root/results/pi05_rm65_policy_window_v2_30k.json"
norm_report="$project_root/results/rm65_sim_policy_train_norm_stats.json"
norm_asset="$openpi_root/assets/pi05_rm65_lora/$repo_id/norm_stats.json"

case "$mode" in
  start)
    resume_args=()
    preflight_only=false
    ;;
  resume)
    resume_args=(--resume)
    preflight_only=false
    ;;
  preflight)
    resume_args=()
    preflight_only=true
    ;;
  *)
    echo "usage: $0 [start|resume|preflight]" >&2
    exit 2
    ;;
esac

if [[ "$preflight_only" == false ]] && pgrep -f '[t]rain_rm65_pi05.py' >/dev/null; then
  echo "ERROR: another RM65 pi0.5 training process is already running" >&2
  exit 2
fi

python3 - "$project_root" "$norm_report" "$norm_asset" <<'PY'
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

project = Path(sys.argv[1])
norm_report_path = Path(sys.argv[2])
norm_asset = Path(sys.argv[3])
required = {
    "train contract": project / "results/rm65_sim_policy_train_openpi_validation.json",
    "validation contract": project / "results/rm65_sim_policy_validation_openpi_validation.json",
    "transition continuity": project / "results/rm65_policy_window_transitions.json",
    "start ambiguity": project / "results/rm65_policy_start_ambiguity.json",
}
for label, path in required.items():
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("status") != "pass":
        raise SystemExit(f"{label} report is not PASS: {path}")
norm_report = json.loads(norm_report_path.read_text(encoding="utf-8"))
if norm_report.get("status") != "pass":
    raise SystemExit(f"normalization report is not PASS: {norm_report_path}")
if not norm_asset.is_file():
    raise SystemExit(f"OpenPI normalization asset is missing: {norm_asset}")
actual_hash = hashlib.sha256(norm_asset.read_bytes()).hexdigest()
if actual_hash != norm_report.get("sha256"):
    raise SystemExit(
        f"normalization hash mismatch: expected {norm_report.get('sha256')}, got {actual_hash}"
    )
print(f"RM65_POLICY_WINDOW_PREFLIGHT=PASS sha256={actual_hash}")
PY

if [[ "$preflight_only" == true ]]; then
  echo "RM65_POLICY_WINDOW_TRAINING_NOT_STARTED=true"
  exit 0
fi

cd "$project_root"
exec "$openpi_root/.venv/bin/python" scripts/train_rm65_pi05.py \
  --repo-id "$repo_id" \
  --exp-name "$exp_name" \
  --num-train-steps 30000 \
  --batch-size 1 \
  --save-interval 5000 \
  --log-interval 100 \
  --report "$report" \
  "${resume_args[@]}"
