# V5 safety audit finding — 2026-09-30

Baseline c413498; code/config unchanged. Success and repeatability gates passed, but these do not establish safety acceptance.

Raw run1/confirm_v5_013/task_report.json reports simulation_safety_abort_reason=cube_outside_workspace_envelope, first violation at action_chunk_063. Post-control settle_a displacement is 6.546821067715357 m; settle_b_final displacement is 13.437208133356426 m versus configured 1 m envelope. This is a material simulation failure, not a harmless placement miss. Policy abort detection did not prevent subsequent settling physics from continuing. Preserve the raw evidence and do not describe this release as universally safe or fully accepted.

Next investigation: verify all 60 post-control checks, distinguish the other failed outcomes, inspect the abort-to-settle control flow and determine a simulation-only fix with regression checks. Any policy/control change requires a new version and separately reported validation; retain original three-run scores unchanged. Checkpoint and evaluation release backup remains outstanding. No code changed in this audit.
