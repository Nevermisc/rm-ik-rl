#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="${OPENPI_CONTAINER_NAME:-libero-openpi_server-1}"
docker stop "${CONTAINER_NAME}"
echo "π0.5 服务已停止。"
