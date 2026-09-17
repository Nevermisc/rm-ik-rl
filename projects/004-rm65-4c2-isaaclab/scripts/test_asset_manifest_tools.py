#!/usr/bin/env python3
"""Check hashing and comparison used for lab-computer migration."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parent
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from compare_asset_manifests import compare_manifests, load_manifest


def create_manifest(directory: Path, output: Path, label: str) -> None:
    subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_ROOT / "hash_asset_tree.py"),
            str(directory),
            "--output",
            str(output),
            "--label",
            label,
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = root / "source"
        destination = root / "destination"
        source.mkdir()
        destination.mkdir()
        (source / "model.urdf").write_text("robot", encoding="utf-8")
        (source / "mesh.stl").write_bytes(b"mesh")
        (destination / "model.urdf").write_text("robot", encoding="utf-8")
        (destination / "mesh.stl").write_bytes(b"mesh")
        source_manifest = root / "source.json"
        destination_manifest = root / "destination.json"
        create_manifest(source, source_manifest, "source")
        create_manifest(destination, destination_manifest, "destination")
        identical = compare_manifests(
            load_manifest(source_manifest), load_manifest(destination_manifest)
        )
        (destination / "mesh.stl").write_bytes(b"changed")
        create_manifest(destination, destination_manifest, "destination")
        changed = compare_manifests(
            load_manifest(source_manifest), load_manifest(destination_manifest)
        )
        passed = (
            identical["status"] == "pass"
            and changed["status"] == "fail"
            and [item["path"] for item in changed["changed_files"]] == ["mesh.stl"]
        )
        print(
            json.dumps(
                {
                    "status": "pass" if passed else "fail",
                    "identical_tree_detected": identical["status"] == "pass",
                    "changed_file_detected": changed["status"] == "fail",
                },
                indent=2,
            )
        )
        return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
