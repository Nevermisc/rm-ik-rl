# RM65-B + pi0.5 v5 simulation deployment

Scope: Isaac Lab simulation only. No real robot deployment is validated here.

## Validated artifact

Run from `/home/chengyu/robot-learning/rm-ik-rl/projects/004-rm65-4c2-isaaclab` on the existing configured server. OpenPI environment: `/home/chengyu/robot-learning/openpi/.venv`. Model: `outputs/openpi_checkpoints/pi05_rm65_lora/rm65_failure_correction_v5_lora_4k/3999`; dataset/normalization ID: `local/rm65_sim_failure_correction_v5_train`. Do not pair with another version's normalization. Training used 150 episodes and 4000 incremental steps from v4/5999.

Formal results before safety patch: 19/20,18/20,19/20; 56/60 overall. Frozen repeatability gate passed at 95% consistency and one outcome-flip case. Runtime patch 0b066dc skips remaining settling after a detected safety abort; regression coverage 2649cc4 passes four cases. Post-patch diagnostic replay:19/20, no abort branch activated. It does not replace original formal results.

Second post-patch replay also scored19/20 without an abort. Controlled Isaac diagnostic (3614168, result f1ecdea) exercised the actual settling block with a real cube and measured0/120/240 physics steps for existing abort/settle-A detection/normal cases. It deliberately excludes the robot and policy, so it validates the settling branch, not prevention of the original fall. Its report passed but application shutdown hung; the diagnostic process was terminated after preserving results.

## Reproduce checks

```bash
bash scripts/evaluate_rm65_pi05_failure_correction_v5.sh preflight
bash scripts/evaluate_rm65_pi05_failure_correction_v5.sh offline
```

The existing `run1`, `run2`, `run3` entrypoints refer to historical output directories; do not use them to claim a fresh post-patch evaluation. For a new run use a NEW, absent output directory and summary path:

```bash
python3 scripts/run_pi05_rm65_closed_loop_suite.py \
  --checkpoint outputs/openpi_checkpoints/pi05_rm65_lora/rm65_failure_correction_v5_lora_4k/3999 \
  --repo-id local/rm65_sim_failure_correction_v5_train \
  --plan config/rm65_pi05_failure_correction_v5_confirmation_20.json \
  --output-root datasets/rm65_pi05_v5_user_replay_001 \
  --summary results/rm65_pi05_v5_user_replay_001_summary.json
```

Run one suite at a time. Preserve all failures. Reusing these conditions after tuning is development evaluation, not a fresh independent score.

## Known limits and recovery

Formal case013 failed all three runs; run1 had cube workspace escape. Its underlying cause remains unresolved. Safety patch prevents subsequent settling after detection but does not prevent initial escape or add per-physics-step checks. Rendering varies despite matched physical states and policy noise; outcomes are not fully deterministic. Never interpret offline PASS or 95% success as universal safety.

Local independent release backup: `RM65_DATA_BACKUP_DO_NOT_GIT/v5_release_2026_09_30`, relative to the user's robot learning workspace. It preserves both2000/3999 checkpoints, normalization and four raw evaluation roots; independent per-file tree comparison passed for all seven assets. Training raw v5 data are separately backed up in `v5_collection_2026_09_29`. Do not commit datasets/checkpoints to Git. Source/backup inventories in results provide recovery verification; retain originals when testing recovery.

Second diagnostic replay is separately preserved in `RM65_DATA_BACKUP_DO_NOT_GIT/v5_safetyfix_run2_2026_09_30`:21,960 files,841,307,014 bytes independently verified. This incremental copy does not modify the frozen seven-asset archive.
