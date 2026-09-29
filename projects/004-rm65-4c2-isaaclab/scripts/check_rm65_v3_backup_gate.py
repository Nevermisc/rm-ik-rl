#!/usr/bin/env python3
"""Fail closed unless the independent RM65 v3 backup matches its source manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_ASSET_IDS = {
    "base_expert_dataset_v1",
    "failure_correction_expert_v1",
    "failure_correction_v3_lerobot",
    "policy_window_v2_checkpoint_29999",
    "failure_correction_v3_checkpoint_9999",
    "failure_correction_v3_norm_stats",
    "fresh_confirmation_run1",
    "repeatability_run2",
    "repeatability_run3",
}
EXPECTED_TOTAL_BYTES = 19_561_366_749


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_backup_gate(
    backup: dict[str, Any], source: dict[str, Any], source_manifest_sha256: str
) -> dict[str, Any]:
    assets = backup.get("assets", [])
    source_assets = source.get("assets", [])
    asset_ids = {item.get("asset_id") for item in assets}
    source_asset_ids = {item.get("asset_id") for item in source_assets}
    checks = {
        "backup_schema": backup.get("schema") == "rm65_data_preservation_manifest_v1",
        "source_schema": source.get("schema") == "rm65_data_preservation_manifest_v1",
        "same_spec_id": backup.get("spec_id") == source.get("spec_id"),
        "backup_location": backup.get("location") == "backup",
        "backup_inventory_pass": backup.get("inventory_status") == "pass",
        "backup_comparison_pass": backup.get("comparison_status") == "pass",
        "nine_expected_assets": asset_ids == EXPECTED_ASSET_IDS,
        "source_has_same_assets": source_asset_ids == EXPECTED_ASSET_IDS,
        "all_assets_match_reference": len(assets) == 9
        and all(item.get("matches_reference") is True for item in assets),
        "total_bytes_match_frozen_inventory": backup.get("total_bytes")
        == source.get("total_bytes")
        == EXPECTED_TOTAL_BYTES,
        "reference_manifest_sha256": backup.get("reference_manifest_sha256")
        == source_manifest_sha256,
        "simulation_only_provenance": backup.get("real_robot_command_sent") is False,
    }
    return {
        "schema": "rm65_v3_backup_gate_v1",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "asset_count": len(assets),
        "total_bytes": backup.get("total_bytes"),
        "source_manifest_sha256": source_manifest_sha256,
        "verified_copy_count": 2 if all(checks.values()) else 1,
        "real_robot_command_sent": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup-manifest", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    backup = json.loads(args.backup_manifest.read_text(encoding="utf-8"))
    source = json.loads(args.source_manifest.read_text(encoding="utf-8"))
    report = validate_backup_gate(backup, source, sha256_file(args.source_manifest))
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
