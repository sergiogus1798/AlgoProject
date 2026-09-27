---
q: why SQX deletes strategies, databank sync removes sqx files, ClearDatabanks wipes, auto-sync every hour, closing SQX deletes strategies, databank flow at risk, partial load pruned
tag: 🔬  date: 2026-09-27  see: databanks/sync-only-touches-loaded, databanks/snapshot-before-restart, databanks/databank-verbs
---
# Memory is the source of truth: a sync deletes on-disk .sqx not held in memory
Applies to every sync of a **loaded** databank — the hourly auto-sync as much as shutdown. Loss paths:
a `ClearDatabanks` task empties memory and the next sync deletes the files; a partially loaded databank
is pruned to that partial set. Before running a project read its **Databank flow** table:
`sqx/inspect/dump_project.py <PROJECT>`. Not: "closing SQX deletes strategies" — misdiagnosis.

## Evidence
- 📓 Log `user/log/StrategyQuant/log_YYYY_MM_DD.log`:
  `'Project - USDJPY/WFM' saved - files before sync 248 / after sync 36 / saved 36 / removed 248`
  (an `Auto-sync every 1 hour` tick).
- ⚠️ Not: "every project on this install ends `ClearDatabanks` in an unconditional loop" — `sqx/inspect/project_map.py`
  ignored a task's `active` attribute until 2026-09-27 (`OPEN.md` issue 10). Of 15 renderable projects only
  4 actually loop unconditionally (AUDJPY task 19, XAUUSD task 16, SP500_H1 task 18, GBPJPY_H1 task 5);
  USDJPY, USDCHF, EURUSD, CADJPY_H1 have the `GoToTask` disabled or conditional. Read a project's own
  **Databank flow** table (`active`-aware since the fix) before trusting which of its `ClearDatabanks`
  tasks a run will actually reach. GBPJPY clears `OOS` (its only at-risk databank, not 3); SP500 H1 clears its `WFM`.
- Old per-project docs under `docs/` are retired; regenerate (`OPEN.md`).
- 📓 Large databanks sync slowly: XAUUSD `WFM` **826 s**. Partial-load pruning hits databanks no
  `ClearDatabanks` touches.
