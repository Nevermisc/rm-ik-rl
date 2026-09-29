# V5 closed-loop evaluation started — 2026-09-29

Prior evidence commit 90a3f6d; code/config unchanged (a30546f, v4-fc-wip.059).

Checkpoint inference PASS and offline held-out validation PASS on 9 episodes / 45 observations. Offline PASS establishes finite shape-correct actions, not task success. These reports are preserved with this log.

Confirmed run1 output directory absent, then launched existing evaluate_rm65_pi05_failure_correction_v5.sh run1 using frozen fresh 20-case confirmation plan and v5/3999. Runner log: results/rm65_pi05_failure_correction_v5_confirmation_run1_runner.log. Do not alter conditions based on these results. Next: inspect completion and failures, continue the planned repeats and repeatability analysis, and report acceptance without conflating offline validation with closed-loop success. No code/config changes or real robot commands.
