#!/usr/bin/env bash
# Run INSIDE the laboratory desktop terminal, independent of SSH lifetime.
set -uo pipefail
cd "$(dirname "$0")/.."
run_id="${1:?run id required}"
mode="${2:-free}"
if [[ ! "$run_id" =~ ^[a-zA-Z0-9_]+$ ]]; then exit 2; fi
log="results/household_visible_${run_id}.log"
if [[ -e "$log" ]]; then echo 'Refusing to overwrite existing log'; exit 2; fi
export PYTHONUNBUFFERED=1
bash scripts/run_household_visible_demo.sh "$run_id" "$mode" 2>&1 | tee "$log"
result=${PIPESTATUS[0]}
echo "Experiment exit=$result. Results require JSON validation, not the window alone."
echo 'Experiment has stopped. Press Enter to close this terminal.'
read -r _
exit "$result"
