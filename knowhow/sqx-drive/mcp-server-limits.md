---
q: what can the sqx MCP server do; load a project into the running master; project missing from list silently; config.xml references missing task files; Infinox_SP500ft_H4_HighPrecision; graft_tasks
tag: 🔬  date: 2026-09-21  see: sqx-drive/which-endpoint, sqx-format/project-cfx
---
# MCP on the master is read-only plus run/stop; a project that fails to load vanishes silently
MCP verbs: `list_projects`, `list_databanks`, `list_strategies`, `get_strategy_stats`, `run_project`,
`stop_project`. No import/loadconfig/config-write. Only route into a running master: GUI Project → Load config.
Diff the live project list against `user/projects/` — a project the GUI cannot load is omitted with no error.
Known permanent gap (owner, 2026-09-21: not repaired): 14 listed vs 15 dirs, hourly sync error keeps logging. Don't re-diagnose.

## Evidence
- Missing one: `Infinox_SP500ft_H4_HighPrecision` (`OPEN.md` issue 3).
- Cause class: `config.xml` references task XML members the archive lacks (declares 8 tasks, ships 3).
  `sqx/inspect/project_health.py` scans all projects in one pass; only broken one on this install.
- If ever repaired (owner withdrew the repair 2026-09-21, "not to be run"; the tool itself,
  `sqx/repair/graft_tasks.py`, was removed as dead code once the decision stood — this is what it
  did, for whoever writes it again): graft, don't restore the backup. `project_backup.cfx`
  (2025-10-13) has the old spaced name `Infinox - SP500ft - H4 (High Precision)` (breaks the API,
  hard rule 6), a since-removed `OOS` databank registration, and a `Retest-Task2.xml` reading stale
  `Complete Data Uncorrelated` instead of `Results`. The fix keeps every live member, copies in only
  the 5 absent ones, verifies nothing missing and every named databank registered. SQX closed.
