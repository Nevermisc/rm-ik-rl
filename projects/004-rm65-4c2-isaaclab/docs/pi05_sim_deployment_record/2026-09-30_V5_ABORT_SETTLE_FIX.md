# v4-fc-wip.060 — skip verification settling after safety abort

Baseline 441d7fb. Problem: run1 case013 crossed the workspace envelope at action chunk63, but unconditional settle holds advanced another 240 physics steps. Source inspection confirmed both holds ran regardless of simulation_safety_abort_reason.

Change: skip settle A when an abort already exists; skip settle B when an abort exists either before or after settle A. Preserve the original abort reason and failure result. Add explicit per-stage skipped-for-safety fields to the report. Normal trajectories retain their original 120+120 steps. This prevents additional settling after detection; it does not prevent the initial escape, nor add per-step detection inside a hold.

Validation: Python syntax compilation PASS. Behavioral regression and simulation replay remain pending; do not claim runtime fix verified yet. Existing 60 evaluation reports and scores remain unchanged and describe the earlier version. Next: exercise pre-existing abort, settle-A detection and normal paths with regression checks, then simulation-only replay into new diagnostic outputs. Release backups remain pending. No checkpoints modified or real robot commands issued.
