#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
OPENPI_DIR="${OPENPI_DIR:-${HOME}/robot-learning/openpi}"
CONTAINER_NAME="${OPENPI_CONTAINER_NAME:-libero-openpi_server-1}"
export RM65_PROJECT_DIR="${PROJECT_DIR}"
export SERVER_ARGS="policy:checkpoint --policy.config=pi05_droid_jointpos_polaris --policy.dir=gs://openpi-assets/checkpoints/pi05_droid_jointpos"

cd "${OPENPI_DIR}"
docker compose \
  -f examples/libero/compose.yml \
  -f "${PROJECT_DIR}/config/openpi-gpu-memory.override.yml" \
  up -d --no-build --force-recreate openpi_server

echo "等待 π0.5 DROID 服务监听 8000 端口……"
for _ in $(seq 1 36); do
  if docker logs --tail 60 "${CONTAINER_NAME}" 2>&1 | grep -q "server listening"; then
    echo "PI05_SERVER_READY=PASS"
    exit 0
  fi
  sleep 5
done

echo "π0.5 服务未在 180 秒内启动。" >&2
docker logs --tail 120 "${CONTAINER_NAME}" >&2
exit 1
