#!/usr/bin/env python3
"""Audit an RM65 backup tar before extraction and compare it with a source manifest."""

from __future__ import annotations

import argparse
import json
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any


def path_is_within_prefix(name: PurePosixPath, prefix: PurePosixPath) -> bool:
    parts = name.parts
    prefix_parts = prefix.parts
    return (
        parts == prefix_parts[: len(parts)]
        or parts[: len(prefix_parts)] == prefix_parts
    )


def audit_archive(
    archive_path: Path,
    *,
    required_prefix: str,
    expected_file_count: int,
    expected_total_bytes: int,
) -> dict[str, Any]:
    prefix = PurePosixPath(required_prefix)
    if prefix.is_absolute() or not prefix.parts or ".." in prefix.parts:
        raise ValueError("required prefix must be a safe relative POSIX path")
    seen: set[str] = set()
    unsafe_entries: list[dict[str, str]] = []
    duplicate_entries: list[str] = []
    regular_file_count = 0
    regular_file_bytes = 0
    directory_count = 0
    with tarfile.open(archive_path, mode="r:*") as archive:
        for member in archive:
            raw_name = member.name
            name = PurePosixPath(raw_name)
            reasons = []
            if name.is_absolute() or not name.parts or ".." in name.parts:
                reasons.append("unsafe_path")
            elif not path_is_within_prefix(name, prefix):
                reasons.append("outside_required_prefix")
            normalized = name.as_posix()
            if normalized in seen:
                duplicate_entries.append(normalized)
            seen.add(normalized)
            if member.isdir():
                directory_count += 1
            elif member.isfile():
                regular_file_count += 1
                regular_file_bytes += member.size
            else:
                reasons.append("non_regular_non_directory_entry")
            if reasons:
                unsafe_entries.append(
                    {"name": raw_name, "reason": ",".join(reasons)}
                )
    checks = {
        "no_unsafe_or_special_entries": not unsafe_entries,
        "no_duplicate_entries": not duplicate_entries,
        "regular_file_count_matches_manifest": regular_file_count
        == expected_file_count,
        "regular_file_bytes_match_manifest": regular_file_bytes
        == expected_total_bytes,
    }
    return {
        "schema": "rm65_safe_backup_tar_audit_v1",
        "status": "pass" if all(checks.values()) else "fail",
        "archive_path": str(archive_path.resolve()),
        "required_prefix": prefix.as_posix(),
        "checks": checks,
        "entry_count": len(seen),
        "directory_count": directory_count,
        "regular_file_count": regular_file_count,
        "regular_file_bytes": regular_file_bytes,
        "expected_file_count": expected_file_count,
        "expected_total_bytes": expected_total_bytes,
        "unsafe_entries": unsafe_entries,
        "duplicate_entries": duplicate_entries,
        "real_robot_command_sent": False,
    }


def expected_asset(manifest: dict[str, Any], asset_id: str) -> dict[str, Any]:
    matches = [asset for asset in manifest.get("assets", []) if asset.get("asset_id") == asset_id]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one manifest asset {asset_id!r}")
    asset = matches[0]
    if not isinstance(asset.get("file_count"), int) or not isinstance(
        asset.get("total_bytes"), int
    ):
        raise ValueError("manifest asset lacks integer file_count/total_bytes")
    return asset


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--asset-id", required=True)
    parser.add_argument("--required-prefix", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.source_manifest.read_text(encoding="utf-8"))
    if manifest.get("schema") != "rm65_data_preservation_manifest_v1":
        raise ValueError("unsupported source manifest")
    asset = expected_asset(manifest, args.asset_id)
    report = audit_archive(
        args.archive,
        required_prefix=args.required_prefix,
        expected_file_count=asset["file_count"],
        expected_total_bytes=asset["total_bytes"],
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
