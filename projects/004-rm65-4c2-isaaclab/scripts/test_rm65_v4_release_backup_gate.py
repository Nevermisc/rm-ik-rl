#!/usr/bin/env python3
"""Unit-check the frozen RM65 v4 release backup gate."""

from __future__ import annotations

from copy import deepcopy

from check_rm65_v4_release_backup_gate import (
    EXPECTED_ASSET_IDS,
    EXPECTED_FILE_COUNT,
    EXPECTED_SPEC_ID,
    EXPECTED_TOTAL_BYTES,
    validate_backup_gate,
)


def manifest(location: str) -> dict:
    ids = sorted(EXPECTED_ASSET_IDS)
    file_counts = [1, 1, 1, 22_700, 21_520, 22_362]
    byte_counts = [1_000, 2_000, 1_854, 3_000, 4_000, 5_000]
    byte_counts[-1] += EXPECTED_TOTAL_BYTES - sum(byte_counts)
    assets = []
    for asset_id, file_count, total_bytes in zip(ids, file_counts, byte_counts):
        item = {
            "asset_id": asset_id,
            "file_count": file_count,
            "total_bytes": total_bytes,
            "tree_sha256": "a" * 64,
        }
        if location == "backup":
            item["matches_reference"] = True
        assets.append(item)
    assert sum(item["file_count"] for item in assets) == EXPECTED_FILE_COUNT
    return {
        "schema": "rm65_data_preservation_manifest_v1",
        "spec_id": EXPECTED_SPEC_ID,
        "location": location,
        "inventory_status": "pass",
        "comparison_status": "pass" if location == "backup" else "not_requested",
        "asset_count": len(assets),
        "total_bytes": EXPECTED_TOTAL_BYTES,
        "assets": assets,
        "reference_manifest_sha256": "b" * 64 if location == "backup" else None,
        "real_robot_command_sent": False,
    }


def main() -> int:
    source = manifest("source")
    backup = manifest("backup")
    passed = validate_backup_gate(backup, source, "b" * 64)
    damaged = deepcopy(backup)
    damaged["assets"][1]["matches_reference"] = False
    rejected = validate_backup_gate(damaged, source, "b" * 64)
    ok = bool(
        passed["status"] == "pass"
        and passed["verified_copy_count"] == 2
        and rejected["status"] == "fail"
        and rejected["verified_copy_count"] == 1
    )
    print(f"RM65_V4_RELEASE_BACKUP_GATE_TEST={'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
