# V5 preparation passed; smoke training launched — 2026-09-29

Prior commit 8147fd5; code/config unchanged from a30546f (v4-fc-wip.059).

Observed RM65_FAILURE_CORRECTION_V5_PREPARATION=PASS in preparation_runner.log. Existing pipeline completed conversion, normalization, OpenPI batch validation and training-input gate for the planned 150 episodes. Batch contract includes padded action shape [1,10,32] and expected original RM65 state/action dimension 7.

Started train_rm65_pi05_failure_correction_v5.sh smoke only after confirming its output directory did not exist. It uses a separate smoke experiment, two steps, frozen v4/5999 initialization and v5 data. Log: results/rm65_pi05_failure_correction_v5_smoke_runner.log. Smoke completion/checkpoint persistence remain to be verified before formal 4000-step training. No code changes or real robot commands.
