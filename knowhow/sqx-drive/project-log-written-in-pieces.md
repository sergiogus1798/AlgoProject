---
q: global_log half written; TASK STARTED without Databanks before start; watcher crashed killed build; log says started never finished; writing flag stuck; Recargar databank does nothing; worker preflight refuses after a killed run; running retest has no total; Hechas / total shows ·; 0 % probadas
tag: 🔬  date: 2026-09-29  see: sqx-drive/window-advances-workflow, databanks/sync-deletes-unloaded-files
---
# SQX writes a project's global_log in pieces, and a killed run's «started» stays in the day's log
A second into a task `user/projects/<P>/log/global_log_<day>_<time>.log` holds only `TASK STARTED`
and `Task: <title>, Type: <type>` — «Databanks before start» comes later, **minutes later for a
retest** (still absent 5 min into an MCR over 200). So a running task's total is its input
databank's count on disk (a retest does not change what it reads), and its share is done/total:
the log carries no compute-thread percent for a retest. Parse every line as optional; a status read must never end a watcher whose `finally` stops the worker. And «started,
not finished» in the worker log means «running» only while `core.worker.holding(top)` is non-empty:
a run killed before «Project finished» otherwise blocks loads and launches until midnight.

## Evidence
2026-09-28 12:07, «Lanzar en SQX» on Test_USDJPY_donchianUpperCrossUp_M30 (custodian): the build
started, `tasklog.task_runs` raised AttributeError on `BEFORE.search(chunk).group(1)` 10 s in, the
job's `finally` stopped the custodian. `find.writing` then said True all day (no process alive), so
«Recargar databank» queued nothing and both launchers' preflight refused. Fixed in `tasklog.py`,
`advance/run.watch`, `loader/find.writing`, `advance/preflight.busy`; `tests/test_tasklog.py`.

2026-09-29 06:48, «▶ SQX» of step 13 on the same project: MCR 1 Bar ran 5 min with `before == {}`;
En marcha showed «22 / ·», «Ritmo —», and the jobs strip «MCR 1 Bar 0 % · 122 probadas». Fixed in
`progress.state` (total falls back to the input on disk), `ops/pulse` (rate on the task's own
clock) and `advance/run.watch` (percent = done/total).
