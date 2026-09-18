#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="${OPENPI_CONTAINER_NAME:-libero-openpi_server-1}"
docker exec -i "${CONTAINER_NAME}" \
  /.venv/bin/python3 -u /rm65_project/scripts/pi05_interface_dry_run.py \
  --observation /rm65_project/outputs/observation/observation.json \
  --output /rm65_project/outputs/pi05_interface_dry_run.json \
  "$@"
