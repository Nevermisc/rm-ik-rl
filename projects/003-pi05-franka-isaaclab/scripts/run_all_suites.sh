#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SIM_EVALS_DIR="${SIM_EVALS_DIR:-${HOME}/robot-learning/sim-evals}"
ISAACLAB_DIR="${ISAACLAB_DIR:-${HOME}/robot-learning/IsaacLab}"
RUNNER="${SCRIPT_DIR}/run_pi05_franka_robustness_suite.py"

cd "${SIM_EVALS_DIR}"

for suite in baseline robustness audit; do
  for scene in 1 2 3; do
    echo
    echo "运行 suite=${suite}, scene=${scene}"
    PYTHONPATH="${SIM_EVALS_DIR}/src" \
      "${ISAACLAB_DIR}/isaaclab.sh" -p "${RUNNER}" \
      --scene "${scene}" \
      --suite "${suite}" \
      --device cuda:0 \
      --headless
  done
done

echo "全部评测执行完成。结果位于 ${SIM_EVALS_DIR}/runs/pi05_franka_suite/"
