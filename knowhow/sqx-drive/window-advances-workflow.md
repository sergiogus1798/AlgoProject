---
q: Continuar workflow from the window; window deletes discards in SQX; advance next task; curate then start; ui/daemon/advance; preflight refuses busy worker; watcher Project finished; only action=status after start; stop only what it started
tag: 📓  date: 2026-09-28  see: databanks/sync-deletes-unloaded-files, databanks/databank-verbs, sqx-drive/running-a-task-headless
---
# «Continuar workflow»: refuse any sign of use, cut files stopped, start, then only `action=status`
Order (`ui/daemon/advance/run.py`, one conductor-lane job): preflight again → copy the discarded
`.sqx` to `AlgoData/projects/discards/<P>/<D>/<stamp>/` + `verdict.csv` → `apply_verdict.apply`
(install stopped) → ledger row → `stage.apply` (only the next task on) → `worker.start` → wait
with `action=status` → `-project action=start` → `progress.state` until «Project finished» → `stop`.
Refuse, never stop, a worker that is up (Q6); the master is refused before anything else.
Follow SQX's log from offsets marked before `action=start`, yesterday's file too; bound the
start (120 s to «Starting project») and the run (48 h), and stop the worker on any failure.

## Evidence
- 📓 `awake()` (`sqx/variants/execute.py`) polls readiness with `-project action=list`, which
  fills memory from disk (`databanks/databank-verbs`); the window must not send it, so readiness
  is polled with `action=status`, which answers `Error: CLI not ready.` for ~20 s like any verb.
- 📓 `progress.run_state` returns `finished=True` for the last start in the day's log; a project
  run earlier today reads finished before this start is even logged. And `progress.log_lines`
  reads only today's `log_YYYY_MM_DD.log`: a run launched before midnight never shows its start
  in the new file. `ui/daemon/advance/sqxlog.py` reads both days from marked offsets
  (`tests/test_advance_edges.py::test_across_midnight`).
- 📓 `jobs.cancel` kills the job's tree with SIGKILL (`psutil.kill`): the `finally` that stops
  the worker never runs. A cancelled «Continuar» leaves the worker up; stop it by hand.
- 📓 In a `--workflow` project `Results` is the input of `OOS`, the eight MCR and `SPP IS`
  (Test_USDJPY_donchianUpperCrossUp_M30's `project.cfx`). «Next task» = first task, in
  WORKFLOW.md's step order after the databank's own step, whose input is that databank → `OOS`.
- 🤔 Not run live yet (plan 24 §6 awaits the owner); `tests/test_advance.py` fakes every SQX call.
