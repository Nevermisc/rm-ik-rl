#!/usr/bin/env python3
"""Create a portable SHA-256 manifest for a model asset directory."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--label", default="asset_tree")
    args = parser.parse_args()

    root = args.directory.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    files = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": digest.hexdigest(),
            }
        )
    report = {
        "format": "asset_tree_sha256_v1",
        "label": args.label,
        "file_count": len(files),
        "total_bytes": sum(item["bytes"] for item in files),
        "files": files,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("format", "label", "file_count", "total_bytes")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
