# v4-fc-wip.062 — release preservation inventory

Baseline 6a6bafc; runtime code remains 2649cc4. Added seven-asset preservation specification matching actual archived paths: two checkpoints, normalization, three original evaluation runs and post-fix diagnostic run.

Transfer and extraction completed. Local archive SHA256 matches server b36284b7ba5b9cb3e40bbf0843de7348eab8459b7c96de5f2da187dd43a39606; member audit passed. Specification is consumed by the existing manifest builder to independently hash source and extracted backup. Tree comparison is pending; do not claim final two-copy gate yet. No policy changes or real robot commands.
