# ui/daemon/ops — the operation routes: the custodian's pulse, what the workers run, the search ledger

Read-only by construction. The pulse reads `/proc`, today's SQX log of the custodian, its
`sqcli.config` and the daemon's own job logs. The one command anything here can send is
`-project action=status`, through `progress.state`, and only to a worker whose log says a
project is running — the one command the custodian may receive between start and collect
(CLAUDE.md rule 3; it syncs nothing). The master is never asked. The ledger view reads
`AlgoData/ledger/*.jsonl` through `ledger/` and never writes a line.

**Imports from:** `core/`, `ledger/`, `ui/daemon/progress.py`, `ui/daemon/jobs.py` (its `LOGS`),
`ui/text/numbers.py` (`num`, pure Python: the pulse line prints counts as the window does) ·
**Consumed by:** `ui/daemon/routers.py` (`ROUTER`) → `ui/desktop/ops/`

| file | what it does | run it | in → out |
|---|---|---|---|
| `api.py` | `ROUTER`: `GET /api/pulse`, `GET /api/ops/sqx`, `GET /api/ledger?study=` | imported | request → JSON |
| `pulse.py` | One reading of the custodian: `n de N` from the newest job log's `PROGRESS` line — or, for a run started outside the window, the running task's count from the worker's status line (`runs.count`) — rate since the project started, JVM PSS against `-Xmx`, CPU over 0.5 s, `MemAvailable`, how many more backtests fit at the measured (or assumed 10 MB) slope, and the warnings | imported | /proc + logs → dict |
| `runs.py` | What each worker runs now: project and task from its log, done/total from `progress.state`, the percent SQX's log gives or done ÷ total. Nothing when the worker is down or its last start finished | imported | logs + status → list |
| `ledgerview.py` | One study's ledger as JSON: its searches, funnel, segments read, virgin map, blind door of step 20 and pooled N/σ | imported | ledger jsonl → dict |

SQX's own log carries no backtest count. A daemon job that prints `PROGRESS <pct> <n> de <N>`
(`sqx.variants.execute`) gives the whole run's count; a run launched from a terminal gives the
running **task**'s count (the worker's «Strategies generated» over the task's input databank), so
the pulse then shows no rate and no ETA, only how far the task is. A build has no total.
