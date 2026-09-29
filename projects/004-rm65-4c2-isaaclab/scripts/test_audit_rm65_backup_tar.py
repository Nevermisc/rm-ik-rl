#!/usr/bin/env python3
"""Regression checks for safe RM65 backup tar auditing."""

from __future__ import annotations

import io
import tarfile
import tempfile
from pathlib import Path

from audit_rm65_backup_tar import audit_archive


def add_bytes(archive: tarfile.TarFile, name: str, payload: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(payload)
    archive.addfile(info, io.BytesIO(payload))


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        healthy_tar = root / "healthy.tar"
        with tarfile.open(healthy_tar, "w") as archive:
            add_bytes(archive, "datasets/rm65_v5/episode_000000/a.bin", b"abc")
            add_bytes(archive, "datasets/rm65_v5/episode_000001/b.bin", b"defgh")
        healthy = audit_archive(
            healthy_tar,
            required_prefix="datasets/rm65_v5",
            expected_file_count=2,
            expected_total_bytes=8,
        )

        traversal_tar = root / "traversal.tar"
        with tarfile.open(traversal_tar, "w") as archive:
            add_bytes(archive, "datasets/rm65_v5/ok.bin", b"x")
            add_bytes(archive, "../escape.bin", b"y")
        traversal = audit_archive(
            traversal_tar,
            required_prefix="datasets/rm65_v5",
            expected_file_count=2,
            expected_total_bytes=2,
        )

        symlink_tar = root / "symlink.tar"
        with tarfile.open(symlink_tar, "w") as archive:
            info = tarfile.TarInfo("datasets/rm65_v5/link")
            info.type = tarfile.SYMTYPE
            info.linkname = "/tmp/target"
            archive.addfile(info)
        symlink = audit_archive(
            symlink_tar,
            required_prefix="datasets/rm65_v5",
            expected_file_count=0,
            expected_total_bytes=0,
        )

        wrong_inventory = audit_archive(
            healthy_tar,
            required_prefix="datasets/rm65_v5",
            expected_file_count=3,
            expected_total_bytes=8,
        )
    passed = bool(
        healthy["status"] == "pass"
        and traversal["status"] == "fail"
        and traversal["checks"]["no_unsafe_or_special_entries"] is False
        and symlink["status"] == "fail"
        and symlink["checks"]["no_unsafe_or_special_entries"] is False
        and wrong_inventory["status"] == "fail"
        and wrong_inventory["checks"]["regular_file_count_matches_manifest"] is False
    )
    print(f"RM65_SAFE_BACKUP_TAR_AUDIT={'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
