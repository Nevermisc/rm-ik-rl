#!/usr/bin/env bash
set -u

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="${1:-$project_root/outputs/migration_audit}"
mkdir -p "$output_dir"

run_report() {
  local name="$1"
  shift
  {
    echo "command: $*"
    echo "timestamp: $(date -Is)"
    "$@"
  } >"$output_dir/$name.txt" 2>&1 || true
}

run_report system uname -a
run_report os_release cat /etc/os-release
run_report cpu lscpu
run_report memory free -h
run_report disks lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS,MODEL,SERIAL
run_report filesystem df -hT
run_report gpu nvidia-smi
run_report docker_version docker version
run_report docker_containers docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
run_report docker_images docker image ls --digests --no-trunc
run_report docker_volumes docker volume ls
run_report tailscale tailscale status
run_report network ip -brief address

directories=(
  "$HOME/robot-learning/004-rm65-4c2-isaaclab"
  "$HOME/robot-learning/openpi"
  "$HOME/robot-learning/IsaacLab"
  "$HOME/robot-learning/rm-ik-rl"
  "$HOME/robot-learning/004-rm65-4c2-isaaclab/external/4C2"
  "$HOME/.cache/huggingface"
  "$HOME/.cache/openpi"
)

{
  echo "timestamp: $(date -Is)"
  for directory in "${directories[@]}"; do
    if [[ -e "$directory" ]]; then
      du -sh "$directory"
    else
      echo "MISSING $directory"
    fi
  done
} >"$output_dir/directory_sizes.txt" 2>&1

{
  echo "timestamp: $(date -Is)"
  for directory in "${directories[@]}"; do
    if [[ -d "$directory/.git" ]]; then
      echo "REPOSITORY $directory"
      git -C "$directory" rev-parse HEAD
      git -C "$directory" remote
      git -C "$directory" status --short
    fi
  done
} >"$output_dir/git_state.txt" 2>&1

{
  echo "timestamp: $(date -Is)"
  find "$HOME/robot-learning" -xdev -type f \
    \( -name '*.usd' -o -name '*.urdf' -o -name '*.safetensors' \
       -o -name 'metadata.json' -o -name 'episode.npz' -o -name 'norm_stats.json' \) \
    -printf '%s\t%p\n' 2>/dev/null | sort -nr
} >"$output_dir/important_files.txt"

if command -v docker >/dev/null 2>&1; then
  for container in $(docker ps -a --format '{{.Names}}'); do
    docker inspect --format \
      'name={{.Name}} image={{.Config.Image}} runtime={{.HostConfig.Runtime}} mounts={{json .Mounts}} device_requests={{json .HostConfig.DeviceRequests}}' \
      "$container" >"$output_dir/docker_runtime_${container}.txt" 2>/dev/null || true
  done
fi

python3 - "$output_dir" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
files = sorted(path.name for path in root.iterdir() if path.is_file())
report = {
    "status": "complete",
    "sensitive_values_collected": False,
    "report_file_count": len(files),
    "report_files": files,
}
(root / "audit_summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
PY

echo "LAB_MIGRATION_AUDIT=$output_dir"
