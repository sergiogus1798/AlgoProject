# ui/daemon/ops — the operation routes: the custodian's pulse, what the workers run, the search ledger

Read-only by construction. The pulse reads `/proc`, today's SQX log of the custodian, its
`sqcli.config` and the daemon's own job logs. The one command anything here can send is
`-project action=status`, through `progress.state`, and only to a worker whose log says a
project is running — the one command the custodian may receive between start and collect
(CLAUDE.md rule 3; it syncs nothing). The master is never asked. The ledger view reads
`AlgoData/ledger/*.jsonl` through `ledger/` and never writes a line.

**Imports from:** `core/`, `ledger/`, `sqx/progress.py`, `sqx/jobs.py` (its `LOGS`),
`ui/text/numbers.py` (`num`, pure Python: the pulse line prints counts as the window does) ·
**Consumed by:** `ui/daemon/routers.py` (`ROUTER`) → `ui/desktop/ops/`

| file | what it does | run it | in → out |
|---|---|---|---|
| `api.py` | The operation routes: the custodian's pulse, what each worker runs, and the search ledger. | imported | request → JSON |
| `ledgerview.py` | The search ledger as the window reads it: searches, funnel and history spent, one study at a time. | imported | ledger jsonl → dict |
| `pulse.py` | The custodian's pulse: backtests done of total, JVM against its ceiling, CPU, free RAM — files only. | imported | /proc + logs → dict |
| `runs.py` | What each SQX worker runs right now and how far its task is: the SQX bars of the jobs strip. | imported | logs + status → list |
| `steps.py` | «En marcha» in the workflow's order: SQX tasks and Python steps in one list, WFC counted by mother. | imported | project → dict |

SQX's own log carries no backtest count. A daemon job that prints `PROGRESS <pct> <n> de <N>`
(`sqx.variants.execute`) gives the whole run's count; a run launched from a terminal gives the
running **task**'s count (the worker's «Strategies generated» over the task's input databank), so
the pulse then shows no rate and no ETA, only how far the task is. A build has no total.
