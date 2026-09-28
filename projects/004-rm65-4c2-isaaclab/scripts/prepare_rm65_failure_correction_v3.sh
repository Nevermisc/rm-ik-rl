#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
openpi_root="${OPENPI_ROOT:-/home/chengyu/robot-learning/openpi}"
repo_id="local/rm65_sim_failure_correction_v3_train"
base_dataset="$project_root/datasets/rm65_scripted_v1"
correction_dataset="$project_root/datasets/rm65_pi05_failure_correction_expert_v1"
correction_plan="$project_root/config/rm65_pi05_failure_correction_expert_plan_v1.json"
correction_summary="$project_root/results/rm65_pi05_failure_correction_expert_v1_summary.json"
conversion_report="$project_root/results/rm65_pi05_failure_correction_v3_conversion.json"
norm_report="$project_root/results/rm65_pi05_failure_correction_v3_norm_stats.json"
validation_report="$project_root/results/rm65_pi05_failure_correction_v3_openpi_validation.json"

cd "$project_root"
mkdir -p results

python3 scripts/summarize_expert_dataset.py \
  "$correction_dataset" \
  --plan "$correction_plan" \
  --output "$correction_summary"

python3 - "$correction_summary" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if report.get("status") != "pass":
    raise SystemExit("failure-correction expert summary is not PASS")
if report.get("episode_count") != 30 or report.get("passed_episode_count") != 30:
    raise SystemExit(f"expected 30/30 usable correction episodes, got {report.get('passed_episode_count')}/{report.get('episode_count')}")
if report.get("collection_plan_coverage", {}).get("status") != "pass":
    raise SystemExit("failure-correction collection-plan coverage is not PASS")
print("RM65_FAILURE_CORRECTION_EXPERT_GATE=PASS")
PY

PYTHONPATH=. "$openpi_root/.venv/bin/python" \
  scripts/convert_expert_episodes_to_lerobot.py \
  "$base_dataset" \
  "$correction_dataset" \
  --repo-id "$repo_id" \
  --split train \
  --policy-window \
  --overwrite \
  --report "$conversion_report"

PYTHONPATH=. "$openpi_root/.venv/bin/python" \
  scripts/compute_rm65_norm_stats.py \
  --repo-id "$repo_id" \
  --batch-size 64 \
  --output "$norm_report"

PYTHONPATH=. "$openpi_root/.venv/bin/python" \
  scripts/validate_rm65_openpi_data.py \
  --repo-id "$repo_id" \
  --output "$validation_report"

python3 - "$conversion_report" "$norm_report" "$validation_report" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

conversion, norm, validation = (
    json.loads(Path(path).read_text(encoding="utf-8")) for path in sys.argv[1:]
)
if conversion.get("status") != "pass":
    raise SystemExit("conversion report is not PASS")
if conversion.get("episode_count") != 66:
    raise SystemExit(f"expected 66 combined training episodes, got {conversion.get('episode_count')}")
if not conversion.get("policy_window"):
    raise SystemExit("combined dataset was not built with the policy window")
if norm.get("status") != "pass" or validation.get("status") != "pass":
    raise SystemExit("normalization or OpenPI data validation is not PASS")
print("RM65_FAILURE_CORRECTION_V3_PREPARATION=PASS")
PY

