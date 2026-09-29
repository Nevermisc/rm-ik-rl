#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mode="${1:-source}"
backup_root="${2:-${RM65_V5_BACKUP_ROOT:-}}"
spec="$project_root/config/rm65_pi05_v5_collection_preservation_assets.json"
source_manifest="$project_root/results/rm65_pi05_v5_collection_source_manifest.json"
backup_manifest="$project_root/results/rm65_pi05_v5_collection_backup_manifest.json"
backup_gate="$project_root/results/rm65_pi05_v5_collection_backup_gate.json"

cd "$project_root"
case "$mode" in
  source)
    python3 scripts/build_data_preservation_manifest.py \
      --spec "$spec" \
      --location source \
      --root "project=$project_root" \
      --output "$source_manifest"
    echo "RM65_V5_COLLECTION_SOURCE_MANIFEST=PASS"
    ;;
  verify)
    if [[ -z "$backup_root" ]]; then
      echo "usage: $0 verify BACKUP_ROOT" >&2
      exit 2
    fi
    if [[ ! -f "$source_manifest" ]]; then
      echo "ERROR: source manifest is missing: $source_manifest" >&2
      exit 2
    fi
    python3 scripts/build_data_preservation_manifest.py \
      --spec "$spec" \
      --location backup \
      --root "backup=$backup_root" \
      --reference "$source_manifest" \
      --output "$backup_manifest"
    python3 scripts/check_rm65_v5_collection_backup_gate.py \
      --backup-manifest "$backup_manifest" \
      --source-manifest "$source_manifest" \
      --output "$backup_gate" >/dev/null
    echo "RM65_V5_COLLECTION_BACKUP_GATE=PASS"
    ;;
  *)
    echo "usage: $0 [source|verify BACKUP_ROOT]" >&2
    exit 2
    ;;
esac
