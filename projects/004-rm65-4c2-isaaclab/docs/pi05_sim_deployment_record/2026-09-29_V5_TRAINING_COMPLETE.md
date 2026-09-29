# V5 formal training completed — 2026-09-29

Previous commit 0149988 confirmed remotely. Code/config baseline a30546f (v4-fc-wip.059), unchanged.

Formal report results/pi05_rm65_failure_correction_v5_4k.json status PASS, 4000 steps completed. Training process no longer running; checkpoint directory contains 2000 and 3999. Latest checkpoint 3999. These observations establish training completion, not deployment acceptance.

Started existing evaluation entrypoint in offline mode. Log: results/rm65_pi05_failure_correction_v5_offline_runner.log. It performs checkpoint inference validation and offline validation on the original validation split before frozen fresh-condition closed-loop trials. Results pending; do not claim final success. Existing unrelated v3 backup-gate Git modification remains untouched. No code changes or real robot commands.
