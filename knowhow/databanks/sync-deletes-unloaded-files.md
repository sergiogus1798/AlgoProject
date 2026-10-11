---
q: Why does a databank sync delete .sqx files that were not loaded in memory — and is a databank nobody opened safe?
kw: does a sync prune a databank nobody opened, unloaded databank safe on restart, removed 0 log, starting a worker for other work endangers batch, why SQX deletes strategies, databank sync removes sqx files, ClearDatabanks wipes, auto-sync every hour, closing SQX deletes strategies, databank flow at risk, partial load pruned, Cannot process strategy InterruptedException, strategy lost at stop, two syncs at once
tag: 🔬  date: 2026-10-11  see: databanks/snapshot-before-restart, databanks/databank-verbs
---
# Memory is the source of truth: a sync deletes on-disk .sqx not held in memory
Applies to every sync of a **loaded** databank — the hourly auto-sync as much as shutdown. Loss paths:
a `ClearDatabanks` task empties memory and the next sync deletes the files; a partially loaded databank
is pruned to that partial set; and **two syncs of one databank at once** (a periodic one when
`-exit`'s shutdown sync starts) interrupt a strategy's lock — «Cannot process strategy 'X'»,
InterruptedException — and the periodic one then deletes X's file. «Lanzar en SQX» restores such
a file from its pre-run snapshot (`launch.run.restore`). Before running a project read its **Databank flow** table:
`sqx/inspect/dump_project.py <PROJECT>`. Not: "closing SQX deletes strategies" — misdiagnosis. Narrowing: a sync touches only **loaded** databanks — one nobody opened is not pruned (Evidence, 2026-09-23); not an all-clear.

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

2026-09-29 13:04, stop after the WFM of Test_USDJPY_donchianUpperCrossUp_M30: periodic sync of
«Retest Markets - Family» (38 s) overlapped the API sync of `-exit`; 13:04:05 «Cannot process
strategy 'Strategy 9.11.67'»; «files before sync 200 / after sync 199 / removed 1». Restored from
`AlgoData/projects/snapshots/…/20260929-120337`.

📓 Narrowing (🔬 2026-09-23, merged from the retired `sync-only-touches-loaded`): a sync touches only databanks that were **loaded**; one nobody opened is not pruned — another session starting the install for unrelated work does not by itself endanger it. Loss needs a databank loaded and then emptied or partly filled. ⚠️ Not an all-clear: keep the no-commands-between-start-and-collect discipline and the snapshot.

Unopened databank stays intact (custodian log `log_2026_09_23.log`): 26 `removed` fields, all `removed 0`, across ~9 start/stop cycles; `Retester/RetestOut` never in memory kept its 962 `.sqx`; the cycle that loaded it logged `files before sync 962 / after sync 962 / removed 0`. The USDJPY `before 248 / after 36` line is a `ClearDatabanks` case. 🤔 First reading, not luck: the files were never pruning candidates.
