#!/usr/bin/env python3
"""Regression tests for compact cross-machine data-preservation manifests."""

from __future__ import annotations

import tempfile
from pathlib import Path

from build_data_preservation_manifest import build_manifest


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = root / "source"
        backup = root / "backup"
        (source / "dataset" / "nested").mkdir(parents=True)
        (backup / "mirror" / "nested").mkdir(parents=True)
        (source / "dataset" / "episode.npz").write_bytes(b"episode")
        (source / "dataset" / "nested" / "image.png").write_bytes(b"image")
        (backup / "mirror" / "episode.npz").write_bytes(b"episode")
        (backup / "mirror" / "nested" / "image.png").write_bytes(b"image")
        spec = {
            "schema": "rm65_data_preservation_spec_v1",
            "spec_id": "test",
            "assets": [
                {
                    "asset_id": "dataset",
                    "kind": "dataset",
                    "priority": "critical",
                    "reproducibility": "source_of_truth",
                    "locations": {
                        "source": {"root": "source", "path": "dataset"},
                        "backup": {"root": "backup", "path": "mirror"},
                    },
                }
            ],
        }
        source_report = build_manifest(spec, "source", {"source": source})
        identical = build_manifest(spec, "backup", {"backup": backup}, source_report)
        (backup / "mirror" / "episode.npz").write_bytes(b"changed")
        changed = build_manifest(spec, "backup", {"backup": backup}, source_report)

        passed = (
            source_report["inventory_status"] == "pass"
            and source_report["comparison_status"] == "not_requested"
            and identical["comparison_status"] == "pass"
            and changed["comparison_status"] == "fail"
            and identical["assets"][0]["matches_reference"] is True
            and changed["assets"][0]["matches_reference"] is False
        )
        print("DATA_PRESERVATION_MANIFEST_TEST=PASS" if passed else "DATA_PRESERVATION_MANIFEST_TEST=FAIL")
        return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
