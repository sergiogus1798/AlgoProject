---
q: Why did «MCR 6 Exits» sit for hours with no «Task finished» and no error, and what ends a task that does not advance?
kw: MCR 6 Exits hang; All backtest data prepared then nothing; RandomizeExitParameters no stop loss profit target trailing; condition-only exits; MonteCarloRetestPlugin runOnGrid waitForFinish; Cross check exception InterruptedException; task deadline taskcap task-durations.json; jstack does not support the attach mechanism; SIGQUIT swallowed by launcher; CLI not ready is not a hang; ALGO_PRECISION_OVERRIDE not the cause; orders.with_exits
tag: 🔬  date: 2026-10-06  see: sqx-drive/mcr-nullpointer-fastutil-transient, sqx-drive/live-chain-without-restart, sqx-drive/transient-abort-automatic-retry
---
# `RandomizeExitParameters` never returns over strategies with no exit method set — dropped there now; and a task past 3× its record is aborted

«MCR 6 Exits» (3 strategies, USA500 H1, `indicesIBS`) logged `All backtest data prepared`, then nothing for 1 h 40 on ~2-4 cores. The strategies exit by condition only (every `exitMethod="true"` Param at `.None` or 0) and the method perturbs exactly those: its MC sub-jobs wait on each other for ever (`MonteCarloRetestPlugin.runOnGrid → GridClient.waitForFinish`, printed as `Cross check exception: InterruptedException` when `exitapp` ends them).
Not precision (same with and without `ALGO_PRECISION_OVERRIDE=1`), not the batch (MCR 1/2/3/5 finished on the same 3 in 2-5 s).
**Remedy:** `orders.with_exits` reads the input population and `perturbations.usable` drops the method where nothing is set, as `RandomizeMinDistance` is dropped on market-only entries.
**Safety net:** `taskcap` aborts a live task past 3× its title's record (`AlgoData/autopilot/task-durations.json`; floor 20 min, 60 unseen; build excepted); `liverun.close` kills the session, empties the step's outputs, sets its log aside; the campaign's tries restart SQX.

## Evidence
- 🔬 2026-10-06 07:14–08:53, `Test_USA500_H1_indicesIBS`, custodian GUI session (SQX log 4262-32433;
  project log `global_log_20261006_071402.log.descartado`): MCR 1, 2, 3, 5 in 2–5 s; MCR 6 `Batch
  size computed to: 5 … str to test: 3, totalCores: 95` was the project's last line. On `exitapp`
  the task closed as `Project stopped`, `Total tested: 2, Passed: 0, Failed: 2`, `cross check
  exception` 100 % — 5,942 s a strategy, the third never started.
- 🔬 Same day, step 13 alone (`bin/workflow.sh run … --smoke --own-log`), MCR outputs emptied and
  the start's log set aside each time: arm A override=1 (run `20261006-101305`) and arm B doctrine
  precision (`20261006-110206`, `20261006-113419`) — identical: 4.0/2.1/2.2/5.0 s then «MCR 6 Exits»
  silent, aborted by the deadline at 22 min (3× its 448 s record), session killed after the other
  projects' databanks were saved (376 s). The third run's `worker-daemon.log` 12:04:40 holds the
  stacks above for `Strategy 8.5.2750` and `20.14.3711`, threads `Blocking computeThread common`.
- 🔬 Healthy «MCR 6 Exits» runs 09-29 → 10-05 (6 s to 448 s, 5-20 strategies a batch):
  `Test_NIKKEI225_M30_simpleL_live` strategies carry `ExitAfterBars1` and `ATRTrailingStops`;
  the USA500 ones nothing — `orders.with_exits`: NIKKEI OOS True, USA500 OOS and Results False.
- 🔬 Thread dumps: `j64/bin/jstack <pid>` → «The VM does not support the attach mechanism» for
  every PID; `SIGQUIT` to the `./StrategyQuantX` PID (a Go launcher: `zenity`, `sqlogger` in its
  strings) printed nothing to its stdout; `jhsdb` needs `ptrace_scope` 0, it is 1. Dropped.
- 🔬 Arm A's in-session rerun: `CrossTF_Mothers` 7 in memory for 3 files, and arm B's first try 9 —
  `loadFilesToDatabank clear=true` does not empty memory: what the session loaded at start stays
  (6 on disk from the morning's syncs + 3). `live.load` now cuts every held name before loading.
- 📓 Healthy durations seeding the deadline (`grep "Task finished in"` 09-29 → 10-05): MCR 6 Exits
  448 s; MCR 7 OHLC 1,692; MCR 8 Stress 2,568; WFM 3,623; SPP OOS 1,153.
