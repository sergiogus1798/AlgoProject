# ui/daemon/ops — the operation routes: the custodian's pulse and the search ledger

Read-only by construction. The pulse reads `/proc`, today's SQX log of the custodian, its
`sqcli.config` and the daemon's own job logs; it never sends a command to any install — not even
`action=status`, which the custodian may receive but the window has no need to send
(CLAUDE.md rule 3). The ledger view reads `AlgoData/ledger/*.jsonl` through `ledger/` and never
writes a line.

**Imports from:** `core/`, `ledger/`, `ui/daemon/progress.py`, `ui/daemon/jobs.py` (its `LOGS`) ·
**Consumed by:** `ui/daemon/app.py` (`ROUTER`) → `ui/desktop/ops/`

| file | what it does | run it | in → out |
|---|---|---|---|
| `api.py` | `ROUTER`: `GET /api/pulse`, `GET /api/ledger?study=` | imported | request → JSON |
| `pulse.py` | One reading of the custodian: `n de N` from the newest job log's `PROGRESS` line, rate since the project started, JVM PSS against `-Xmx`, CPU over 0.5 s, `MemAvailable`, how many more backtests fit at the measured (or assumed 10 MB) slope, and the warnings | imported | /proc + logs → dict |
| `ledgerview.py` | One study's ledger as JSON: its searches, funnel, segments read, virgin map, blind door of step 20 and pooled N/σ | imported | ledger jsonl → dict |

⚠️ SQX's own log carries no backtest count: `done`/`total` exist only when the run is a daemon
job that prints `PROGRESS <pct> <n> de <N> …` (`sqx.variants.execute`). A run launched from a
terminal session shows `avance ?`, with JVM, CPU and free RAM still read.
