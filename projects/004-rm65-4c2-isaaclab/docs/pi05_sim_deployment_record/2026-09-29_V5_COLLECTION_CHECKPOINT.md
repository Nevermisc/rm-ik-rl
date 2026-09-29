# V5 collection checkpoint — 2026-09-29 18:48 Asia/Singapore

- Code/config baseline: `a30546f`, working version `v4-fc-wip.059`. This checkpoint changes documentation only.
- Verified remote collection runner PID 368223 remains active. Episodes 000000–000014 have metadata with `task_success: true` (15/48). This is a partial observation, not a complete dataset quality gate.
- Prior problem: the 0.85 rad expert attempt exceeded the placement error threshold. The evidence-based 0.845 rad adjustment is committed in the baseline. All four replacement group episodes 000008–000011 now report task success. The rejected attempt remains preserved outside training.
- Method: inspected Git HEAD/status, live collection log, process identity and per-episode task-success fields. A read-only Python probe failed because of PowerShell/SSH quoting; a direct text inspection succeeded. No dataset or code was modified by that failed probe.
- Remaining checks: complete all 48 episodes; verify plan coverage, raw validity and all 12 same-physics/render-diversity groups; create and independently verify a second data copy before conversion; prepare 150 episodes; smoke test then train v5 for 4000 steps; evaluate on the frozen fresh confirmation cases.
- No training or final deployment success is claimed. Existing unrelated Git changes were left untouched.
