#!/usr/bin/env python3
"""Fail closed unless the v4 raw correction collection has two verified copies."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_SPEC_ID = "rm65_pi05_v4_collection_assets_2026_09_29"
EXPECTED_ASSET_ID = "failure_correction_v4_expert_v1"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_backup_gate(
    backup: dict[str, Any], source: dict[str, Any], source_manifest_sha256: str
) -> dict[str, Any]:
    backup_assets = backup.get("assets", [])
    source_assets = source.get("assets", [])
    backup_ids = {item.get("asset_id") for item in backup_assets}
    source_ids = {item.get("asset_id") for item in source_assets}
    source_total = source.get("total_bytes")
    checks = {
        "backup_schema": backup.get("schema") == "rm65_data_preservation_manifest_v1",
        "source_schema": source.get("schema") == "rm65_data_preservation_manifest_v1",
        "frozen_spec_id": backup.get("spec_id")
        == source.get("spec_id")
        == EXPECTED_SPEC_ID,
        "backup_location": backup.get("location") == "backup",
        "source_location": source.get("location") == "source",
        "backup_inventory_pass": backup.get("inventory_status") == "pass",
        "source_inventory_pass": source.get("inventory_status") == "pass",
        "backup_comparison_pass": backup.get("comparison_status") == "pass",
        "one_expected_asset": backup_ids == source_ids == {EXPECTED_ASSET_ID},
        "asset_matches_reference": len(backup_assets) == 1
        and backup_assets[0].get("matches_reference") is True,
        "nonempty_equal_total_bytes": isinstance(source_total, int)
        and source_total > 0
        and backup.get("total_bytes") == source_total,
        "reference_manifest_sha256": backup.get("reference_manifest_sha256")
        == source_manifest_sha256,
        "simulation_only_provenance": backup.get("real_robot_command_sent") is False
        and source.get("real_robot_command_sent") is False,
    }
    passed = all(checks.values())
    return {
        "schema": "rm65_v4_collection_backup_gate_v1",
        "status": "pass" if passed else "fail",
        "checks": checks,
        "asset_count": len(backup_assets),
        "total_bytes": backup.get("total_bytes"),
        "source_manifest_sha256": source_manifest_sha256,
        "verified_copy_count": 2 if passed else 1,
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
    report = validate_backup_gate(backup, source, file_sha256(args.source_manifest))
    text = json.dumps(report, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
