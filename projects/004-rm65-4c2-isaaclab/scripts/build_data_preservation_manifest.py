#!/usr/bin/env python3
"""Build or verify compact SHA-256 manifests for datasets and checkpoints."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "rm65_data_preservation_manifest_v1"


def parse_root(value: str) -> tuple[str, Path]:
    name, separator, raw_path = value.partition("=")
    if not separator or not name or not raw_path:
        raise argparse.ArgumentTypeError("roots must use NAME=PATH")
    return name, Path(raw_path).expanduser().resolve()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compact_tree_hash(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.is_file():
        files = [(".", path)]
    elif path.is_dir():
        files = [
            (item.relative_to(path).as_posix(), item)
            for item in sorted(path.rglob("*"))
            if item.is_file()
        ]
    else:
        raise ValueError(f"unsupported asset type: {path}")

    tree_digest = hashlib.sha256()
    total_bytes = 0
    for relative_path, file_path in files:
        size = file_path.stat().st_size
        digest = file_sha256(file_path)
        total_bytes += size
        record = f"{relative_path}\0{size}\0{digest}\n".encode("utf-8")
        tree_digest.update(record)
    return {
        "file_count": len(files),
        "total_bytes": total_bytes,
        "tree_sha256": tree_digest.hexdigest(),
        "hash_algorithm": "sha256(relative_path\\0bytes\\0file_sha256\\n)_v1",
    }


def load_spec(path: Path) -> dict[str, Any]:
    spec = json.loads(path.read_text(encoding="utf-8"))
    if spec.get("schema") != "rm65_data_preservation_spec_v1":
        raise ValueError(f"unsupported preservation spec: {path}")
    assets = spec.get("assets")
    if not isinstance(assets, list) or not assets:
        raise ValueError("preservation spec must contain a non-empty assets list")
    asset_ids = [asset.get("asset_id") for asset in assets]
    if any(not isinstance(asset_id, str) or not asset_id for asset_id in asset_ids):
        raise ValueError("every asset requires a non-empty asset_id")
    if len(asset_ids) != len(set(asset_ids)):
        raise ValueError("asset_id values must be unique")
    return spec


def build_manifest(
    spec: dict[str, Any],
    location: str,
    roots: dict[str, Path],
    reference: dict[str, Any] | None = None,
) -> dict[str, Any]:
    reference_assets = (
        {item["asset_id"]: item for item in reference.get("assets", [])}
        if reference is not None
        else {}
    )
    records: list[dict[str, Any]] = []
    for asset in spec["assets"]:
        location_spec = asset.get("locations", {}).get(location)
        if not isinstance(location_spec, dict):
            raise ValueError(f"asset {asset['asset_id']} has no {location!r} location")
        root_name = location_spec.get("root")
        relative_path = location_spec.get("path")
        if root_name not in roots:
            raise ValueError(f"root {root_name!r} is not configured")
        if not isinstance(relative_path, str) or not relative_path:
            raise ValueError(f"asset {asset['asset_id']} has an invalid path")
        resolved_path = (roots[root_name] / relative_path).resolve()
        root_path = roots[root_name]
        if resolved_path != root_path and root_path not in resolved_path.parents:
            raise ValueError(f"asset path escapes root: {asset['asset_id']}")

        record = {
            "asset_id": asset["asset_id"],
            "kind": asset.get("kind", "unspecified"),
            "priority": asset.get("priority", "unspecified"),
            "reproducibility": asset.get("reproducibility", "unspecified"),
            "root": root_name,
            "relative_path": relative_path,
            "resolved_path": str(resolved_path),
            **compact_tree_hash(resolved_path),
        }
        if reference is not None:
            expected = reference_assets.get(asset["asset_id"])
            record["matches_reference"] = bool(
                expected
                and record["file_count"] == expected.get("file_count")
                and record["total_bytes"] == expected.get("total_bytes")
                and record["tree_sha256"] == expected.get("tree_sha256")
            )
        records.append(record)

    inventory_passed = len(records) == len(spec["assets"])
    comparison_passed = reference is None or all(
        item.get("matches_reference") for item in records
    )
    return {
        "schema": SCHEMA,
        "spec_id": spec.get("spec_id"),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "location": location,
        "inventory_status": "pass" if inventory_passed else "fail",
        "comparison_status": (
            "not_requested"
            if reference is None
            else ("pass" if comparison_passed else "fail")
        ),
        "asset_count": len(records),
        "total_bytes": sum(item["total_bytes"] for item in records),
        "assets": records,
        "real_robot_command_sent": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--location", choices=("source", "backup"), required=True)
    parser.add_argument("--root", action="append", default=[], type=parse_root)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    roots = dict(args.root)
    if len(roots) != len(args.root):
        raise ValueError("root names must be unique")
    spec = load_spec(args.spec)
    reference = None
    if args.reference is not None:
        reference = json.loads(args.reference.read_text(encoding="utf-8"))
        if reference.get("schema") != SCHEMA:
            raise ValueError(f"unsupported reference manifest: {args.reference}")
        if reference.get("spec_id") != spec.get("spec_id"):
            raise ValueError("reference manifest spec_id does not match")

    report = build_manifest(spec, args.location, roots, reference)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "schema",
                    "spec_id",
                    "location",
                    "inventory_status",
                    "comparison_status",
                    "asset_count",
                    "total_bytes",
                )
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report["inventory_status"] == "pass" and report["comparison_status"] != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
