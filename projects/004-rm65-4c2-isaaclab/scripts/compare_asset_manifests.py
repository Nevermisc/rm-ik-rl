#!/usr/bin/env python3
"""Compare two manifests produced by hash_asset_tree.py."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_manifest(path: Path) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("format") != "asset_tree_sha256_v1":
        raise ValueError(f"unsupported manifest format in {path}")
    files = report.get("files")
    if not isinstance(files, list):
        raise ValueError(f"manifest has no file list: {path}")
    return report


def compare_manifests(source: dict[str, Any], destination: dict[str, Any]) -> dict[str, Any]:
    source_files = {item["path"]: item for item in source["files"]}
    destination_files = {item["path"]: item for item in destination["files"]}
    missing = sorted(source_files.keys() - destination_files.keys())
    extra = sorted(destination_files.keys() - source_files.keys())
    common = sorted(source_files.keys() & destination_files.keys())
    changed = [
        {
            "path": name,
            "source_bytes": source_files[name]["bytes"],
            "destination_bytes": destination_files[name]["bytes"],
            "source_sha256": source_files[name]["sha256"],
            "destination_sha256": destination_files[name]["sha256"],
        }
        for name in common
        if (
            source_files[name]["bytes"] != destination_files[name]["bytes"]
            or source_files[name]["sha256"] != destination_files[name]["sha256"]
        )
    ]
    passed = not missing and not extra and not changed
    return {
        "status": "pass" if passed else "fail",
        "source_label": source.get("label"),
        "destination_label": destination.get("label"),
        "source_file_count": len(source_files),
        "destination_file_count": len(destination_files),
        "missing_files": missing,
        "extra_files": extra,
        "changed_files": changed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = compare_manifests(
        load_manifest(args.source),
        load_manifest(args.destination),
    )
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
