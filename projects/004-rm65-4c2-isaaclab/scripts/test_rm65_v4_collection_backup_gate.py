#!/usr/bin/env python3
"""Unit-check the v4 raw correction collection backup gate."""

from __future__ import annotations

from check_rm65_v4_collection_backup_gate import (
    EXPECTED_ASSET_ID,
    EXPECTED_SPEC_ID,
    validate_backup_gate,
)


def manifest(location: str) -> dict:
    asset = {
        "asset_id": EXPECTED_ASSET_ID,
        "file_count": 100,
        "total_bytes": 123456,
        "tree_sha256": "a" * 64,
    }
    if location == "backup":
        asset["matches_reference"] = True
    return {
        "schema": "rm65_data_preservation_manifest_v1",
        "spec_id": EXPECTED_SPEC_ID,
        "location": location,
        "inventory_status": "pass",
        "comparison_status": "pass" if location == "backup" else "not_requested",
        "asset_count": 1,
        "total_bytes": 123456,
        "assets": [asset],
        "reference_manifest_sha256": "b" * 64 if location == "backup" else None,
        "real_robot_command_sent": False,
    }


def main() -> int:
    source = manifest("source")
    backup = manifest("backup")
    passed_report = validate_backup_gate(backup, source, "b" * 64)
    damaged = manifest("backup")
    damaged["assets"][0]["matches_reference"] = False
    failed_report = validate_backup_gate(damaged, source, "b" * 64)
    passed = bool(
        passed_report["status"] == "pass"
        and passed_report["verified_copy_count"] == 2
        and failed_report["status"] == "fail"
        and failed_report["verified_copy_count"] == 1
    )
    print(f"RM65_V4_COLLECTION_BACKUP_GATE={'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
