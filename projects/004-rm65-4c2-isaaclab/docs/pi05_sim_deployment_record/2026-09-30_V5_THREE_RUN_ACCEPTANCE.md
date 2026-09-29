# V5 three-run success and repeatability gates passed — 2026-09-30

Previous commit 7bf5e69. Code/config unchanged from a30546f (v4-fc-wip.059).

Frozen fresh confirmation results: run1 19/20, run2 18/20, run3 19/20, total 56/60 (93.33%). All three meet the frozen 90% single-run threshold. Existing analyze entrypoint completed with status PASS: 60 valid reports, 19/20 consistent cases (95%), one outcome-flip case. Patterns: 18 pass/pass/pass, one fail/fail/fail, one pass/fail/pass. All initial joint, gripper, physical-state and noise hashes match across repeats; rendered images and raw actions do not match exactly. Do not claim deterministic image/action reproduction or universal success.

Evidence: results/rm65_pi05_failure_correction_v5_repeatability_20x3.json plus retained raw run roots and summaries. Stable failed condition confirm_v5_013 remains a known limitation. No thresholds or conditions were changed during evaluation.

Success and repeatability gates passed; final release work remains: inspect all post-control safety fields and failure reports, independently back up v5 checkpoints/normalization/raw evaluations, and document reproducible simulation deployment with limitations. No real robot deployment or code changes in this step.
