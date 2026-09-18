#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
ISAACLAB_SH="${ISAACLAB_SH:-${HOME}/robot-learning/IsaacLab/isaaclab.sh}"
USD="${RM65_4C2_USD:-${PROJECT_DIR}/generated/rm65_4c2_software.usd}"
OUTPUT_DIR="${PROJECT_DIR}/outputs/observation"
mkdir -p "${OUTPUT_DIR}"

for view in external wrist; do
  echo "采集 ${view} 视图……"
  "${ISAACLAB_SH}" -p "${SCRIPT_DIR}/capture_single_view.py" \
    --usd "${USD}" \
    --view "${view}" \
    --output-dir "${OUTPUT_DIR}" \
    --headless \
    --enable_cameras
done

python3 "${SCRIPT_DIR}/assemble_observation.py" \
  --external "${OUTPUT_DIR}/external.json" \
  --wrist "${OUTPUT_DIR}/wrist.json" \
  --output "${OUTPUT_DIR}/observation.json"
