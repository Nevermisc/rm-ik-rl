# V5 smoke passed and formal training launched — 2026-09-29

Previous commit: 20ee963. Code/config baseline a30546f (v4-fc-wip.059) unchanged.

Two-step smoke report status PASS; process finished and checkpoint 1/params exists. Step 1 loss 0.0006, gradient norm 0.0461, parameter norm 1803.9023. This validates training execution and persistence, not closed-loop task success.

Confirmed formal v5 output did not exist, then launched train_rm65_pi05_failure_correction_v5.sh start. Frozen settings: 150 episodes; initialization v4/5999/params; 4000 steps; batch 1; warmup 200; peak LR 1e-6, decay LR 2.5e-7; save/keep interval 2000. New log: results/rm65_pi05_failure_correction_v5_training_runner.log. No existing v2/v3/v4 checkpoints overwritten. Formal completion is pending.

Next: verify live progress and finite losses, confirm final checkpoint persistence, perform offline checks and frozen fresh-condition evaluation. User reaffirmed work through 2026-09-30 12:00 Asia/Singapore. No code/config updates or real robot commands in this step.
