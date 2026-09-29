# v4-fc-wip.061 — settling regression coverage

Baseline 0b066dc. Added test_rm65_abort_settling.py: executes the actual settling AST block with mocked physics dependencies, rather than duplicating its decisions. Four local tests PASS: prior abort skips both holds; settle-A violation skips B; normal path retains two 120-step holds; final violation is recorded. This does not prove prevention of the original physical escape.

Next run uses the unchanged 20-case plan and checkpoint in a separate safetyfix diagnostic output root; historical three-run acceptance remains immutable. Runtime verification pending, including whether the rare online abort recurs. No policy/checkpoint changes or real robot commands.
