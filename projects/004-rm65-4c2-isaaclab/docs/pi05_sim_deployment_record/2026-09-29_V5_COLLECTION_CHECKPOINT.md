# V5 collection checkpoint — 2026-09-29 18:48 Asia/Singapore

- Code/config baseline: `a30546f`, working version `v4-fc-wip.059`. This checkpoint changes documentation only.
- Verified remote collection runner PID 368223 remains active. Episodes 000000–000014 have metadata with `task_success: true` (15/48). This is a partial observation, not a complete dataset quality gate.
- Prior problem: the 0.85 rad expert attempt exceeded the placement error threshold. The evidence-based 0.845 rad adjustment is committed in the baseline. All four replacement group episodes 000008–000011 now report task success. The rejected attempt remains preserved outside training.
- Method: inspected Git HEAD/status, live collection log, process identity and per-episode task-success fields. A read-only Python probe failed because of PowerShell/SSH quoting; a direct text inspection succeeded. No dataset or code was modified by that failed probe.
- Remaining checks: complete all 48 episodes; verify plan coverage, raw validity and all 12 same-physics/render-diversity groups; create and independently verify a second data copy before conversion; prepare 150 episodes; smoke test then train v5 for 4000 steps; evaluate on the frozen fresh confirmation cases.
- No training or final deployment success is claimed. Existing unrelated Git changes were left untouched.

## Follow-up group audit

- Collection reached 16 metadata files and remains active. Baseline code remains `a30546f`; preceding documentation commit is `c1451ce`.
- Question: do the corrected 0.845 rad group and the next source case preserve identical physics across rendering repeats, rather than merely reporting task success?
- Ran the existing render-group analyzer on completed groups `confirm_v4_010_angle_plus_0p0075` and `confirm_v4_011_angle_minus_0p0125` (episodes 8–15), without touching the active episode.
- Result: PASS for both groups, all 8 episodes valid/successful, 569 frames each. Action, initial state and physical trajectory differences are zero. Both camera streams have diverse corresponding-frame ratio 1.0 in both groups.
- Evidence: `results/rm65_pi05_failure_correction_v5_boundary_and_second_case_groups.json`. This is a selected-group check, not the complete 48-episode acceptance gate. No code/config changes were needed. Continue collection, then full audit and backup.

## Camera initialization interruption and recovery

- Observed 27 metadata files; collection stopped before recording episode 000027. Existing log identifies `RuntimeError: Isaac cameras did not produce usable RGB frames after 30 render ticks; last shapes were ((0,), (0,))`. No episode_000027 directory existed. This is an initialization failure before recording, not evidence of a failed physical task.
- Disk had 2.2 TB available and idle GPU memory usage was 149/16376 MiB. These observations do not establish the underlying camera initialization cause.
- Preserved the original log and resumed the existing collection command with identical plan/seed/thresholds. Existing completed-episode checking skips prior samples; no data were removed or overwritten.
- New log: `results/rm65_pi05_failure_correction_v5_collection_resume_camera_initialization.log`. Runner PID 377358 was verified active; it passed camera initialization and reached CLOSE_START. Full episode and group validation are still pending.
- Code/config baseline unchanged (`a30546f`); preceding evidence commit `c6825a4`. No code fix is claimed. If the initialization failure recurs, investigate rendering startup separately before changing collection semantics.
