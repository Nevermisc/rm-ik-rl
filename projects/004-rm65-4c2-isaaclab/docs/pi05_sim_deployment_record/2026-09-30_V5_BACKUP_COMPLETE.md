# V5 independent release backup verified

Baseline 2df3a19, version .062. No code/config changes.

Source and local extracted backup independently hashed using build_data_preservation_manifest.py. Compared each asset by ID, file count, bytes and tree_sha256: all seven PASS. Total 91,100 files and 15,044,916,493 bytes. Source and backup inventories are committed as compact evidence, not raw data. Local backup root: RM65_DATA_BACKUP_DO_NOT_GIT/v5_release_2026_09_30. Archive SHA256 b36284b7ba5b9cb3e40bbf0843de7348eab8459b7c96de5f2da187dd43a39606 also matches both hosts.

Assets: checkpoints2000 (24 files),3999 (25), normalization(1), formal run1(22030),run2(22600),run3(22080), post-fix replay(24340). Two independent copies verified. The inventory comparison_status fields read not_requested because inventories were built independently; the subsequent explicit per-asset comparison passed.

Remaining: reproducible deployment instructions and safety limitations, further investigation of rare cube escape. Formal success/repeatability gates passed but this is not physical-robot authorization or proof of universal safety.
