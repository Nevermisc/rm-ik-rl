# V5 collection completed — 2026-09-29

Code/config baseline remains a30546f (v4-fc-wip.059); prior documentation commit 565e50e. No code/config change in this update.

Collection resumed after camera startup failure and completed all 48 requested episodes: 27 skipped as previously complete, 21 newly completed. Full summary PASS: 48/48 task successes, 27,312 frames, episode health and exact plan coverage PASS. Full render-group audit PASS: 12/12 physical groups. These are scripted expert results, not pi0.5 evaluation results.

Evidence: results/rm65_pi05_failure_correction_v5_expert_v1_summary.json and results/rm65_pi05_failure_correction_v5_render_groups.json. Source preservation manifest generated successfully: 2,658,008,431 bytes.

Created static archive /tmp/rm65_v5_collection_20260929.tar. SHA256: 8b647e21787421b1ff34621b32bc60d91a4fb153fb32f80fb6243e767b27941a. Transfer started to local RM65_DATA_BACKUP_DO_NOT_GIT/v5_collection_2026_09_29/rm65_v5_collection_20260929.tar. Transfer completion, local archive checksum, safe member audit, extraction and independent file rehash remain pending. Do not treat this as a verified second copy yet.

Next: finish independent backup and two-copy gate, then convert 150 training episodes, smoke test and train v5 for 4000 steps. Preserve checkpoints and frozen fresh confirmation plan. No real robot commands were issued.
