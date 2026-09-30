# Retained step2000 candidate diagnostic

Baselinecdf3a5b; runtime/config unchanged. Current3999 repeatability fails while extended action budget did not help. Inspect retained2000 checkpoint as a distinct development candidate, testing whether later training affected robustness. Both checkpoints already independently backed up; default3999 remains unchanged.

Started checkpoint loading/inference validation using same v5 normalization and a recorded base episode, report results/rm65_v5_step2000_checkpoint_diagnostic.json. Only after this passes may separate closed-loop diagnostic run. Any selection based on reused conditions is development selection, not fresh acceptance; future promotion requires new frozen evaluation conditions. Do not select only favorable trials or overwrite original outcomes. No training,checkpoint mutation or real robot commands.

Afterede5a7e: inference reportPASS, actions[10,7] all finite, validation process exited. Started full20-case development comparison with2000 checkpoint, original120 chunks, output datasets/rm65_pi05_v5_step2000_diagnostic. This is candidate diagnosis despite the suite's standard-settings diagnostic_only flag; it is not a new independent acceptance run. Default checkpoint and prior scores unchanged.
