#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
OPENPI_DIR="${OPENPI_DIR:-${HOME}/robot-learning/openpi}"
CONTAINER_NAME="${OPENPI_CONTAINER_NAME:-libero-openpi_server-1}"

cd "${OPENPI_DIR}"
SERVER_ARGS="policy:checkpoint --policy.config=pi05_droid_jointpos_polaris --policy.dir=gs://openpi-assets/checkpoints/pi05_droid_jointpos" \
docker compose \
  -f examples/libero/compose.yml \
  -f "${PROJECT_DIR}/config/openpi-gpu-memory.override.yml" \
  up -d --no-build --force-recreate openpi_server

echo "等待 π0.5 服务监听 8000 端口……"
for _ in $(seq 1 24); do
  if docker logs --tail 40 "${CONTAINER_NAME}" 2>&1 | grep -q "server listening"; then
    break
  fi
  sleep 5
done

if ! docker logs --tail 40 "${CONTAINER_NAME}" 2>&1 | grep -q "server listening"; then
  echo "π0.5 服务未在预期时间内启动。" >&2
  docker logs --tail 100 "${CONTAINER_NAME}" >&2
  exit 1
fi

echo "开始首次推理预热；RTX 4060 Ti 上约需 2～3 分钟……"
docker exec -i "${CONTAINER_NAME}" /.venv/bin/python3 -u - \
  < "${PROJECT_DIR}/scripts/warmup_pi05_droid.py"
