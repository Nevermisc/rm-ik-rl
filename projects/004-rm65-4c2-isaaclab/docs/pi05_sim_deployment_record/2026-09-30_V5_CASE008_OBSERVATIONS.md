# Case008 exact observation comparison

Baseline083e91f; runtime unchanged. Ran existing exact-policy-observation analyzer on post-fix run1(fail) versus run2(pass) case008, using actual OpenPI resize preprocessing. Capture evidence verified; initial physical-state hashes and chunk-zero noise match, raw action hash differs. Analysis statusPASS means valid comparison, not matching observations or deployment success. Report results/rm65_v5_case008_observation_comparison.json preserves detailed image/action differences.

This narrows the observed divergence to policy inputs/output despite matched initial physics/noise; it does not establish that renderer variation alone caused terminal placement failure. No image filters, action smoothing or thresholds changed. Next inspect magnitudes and compare case013 before choosing any new correction. Historical gates unchanged.
