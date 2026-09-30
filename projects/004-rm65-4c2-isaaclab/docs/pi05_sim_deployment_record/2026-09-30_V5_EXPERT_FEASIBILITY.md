# Exact failed-condition expert feasibility diagnostic

Baseline1bdd754; runtime/config unchanged. Started scripted expert at case013 angle0.86875,source offset(0.01,-0.005),seed792029013 into new datasets/rm65_v5_case013_expert_feasibility. Purpose: test whether the existing expert can supply a feasible correction trajectory at this policy-failure condition. This is a diagnostic expert rollout, not pi0.5 success or training data yet.

No existing evaluation outcomes overwritten. If later used for training, these evaluated conditions must remain development-only and final validation require new frozen conditions. Next inspect expert success/health before deciding whether correction collection is justified. Raw diagnostic preservation pending; no real robot commands.
