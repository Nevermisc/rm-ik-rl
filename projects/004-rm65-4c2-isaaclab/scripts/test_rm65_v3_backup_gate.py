#!/usr/bin/env python3
"""Regression checks for the RM65 v3 independent-backup gate."""

from __future__ import annotations

from check_rm65_v3_backup_gate import (
    EXPECTED_ASSET_IDS,
    EXPECTED_TOTAL_BYTES,
    validate_backup_gate,
)


def manifest(location: str, comparison: str, digest: str) -> dict:
    return {
        "schema": "rm65_data_preservation_manifest_v1",
        "spec_id": "rm65_pi05_v3_core_assets_2026_09_29",
        "location": location,
        "inventory_status": "pass",
        "comparison_status": comparison,
        "asset_count": 9,
        "total_bytes": EXPECTED_TOTAL_BYTES,
        "reference_manifest_sha256": digest,
        "assets": [
            {"asset_id": asset_id, "matches_reference": True}
            for asset_id in sorted(EXPECTED_ASSET_IDS)
        ],
        "real_robot_command_sent": False,
    }


def main() -> int:
    digest = "a" * 64
    source = manifest("source", "not_requested", digest)
    backup = manifest("backup", "pass", digest)
    passed = validate_backup_gate(backup, source, digest)
    corrupted = manifest("backup", "pass", digest)
    corrupted["assets"][0]["matches_reference"] = False
    rejected = validate_backup_gate(corrupted, source, digest)
    ok = (
        passed["status"] == "pass"
        and passed["verified_copy_count"] == 2
        and rejected["status"] == "fail"
        and rejected["verified_copy_count"] == 1
    )
    print("RM65_V3_BACKUP_GATE_TEST=PASS" if ok else "RM65_V3_BACKUP_GATE_TEST=FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
