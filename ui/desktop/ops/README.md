# ui/desktop/ops — OPERACIÓN: «En marcha», «Registro de búsquedas» and the jobs strip

Views only; every figure comes from the daemon (`/api/jobs`, `/api/ops/sqx`, `/api/pulse`,
`/api/progress`, `/api/ledger`). Labels through `glossary.label`, numbers through `numbers.num`.

**Imports from:** `ui/desktop/client.py`, `theme.py`, `glossary.py`, `numbers.py`,
`durations.py`, `resultspanel.py`, `selection.py` · **Consumed by:** `ui/desktop/shell.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `jobsbar.py` | `JobsBar(QWidget)`: status-bar strip polling `/api/jobs` every 2 s and `/api/ops/sqx` every 16 s — running jobs with their state and a 0-100 % bar (the job's last `PROGRESS` line), queued ones with their position, a ✕ per job (`POST /api/jobs/{id}/cancel`), each SQX run on a worker with its task, count and bar (no ✕: the window never stops SQX), failures counted | imported | jobs → strip |
| `pulse.py` | `Pulse(QFrame term)`: the custodian's one-line pulse, its figures each with a tooltip saying where it comes from, warnings in red, and the last 30 readings (in memory). Polls every 60 s only while shown; embedded in `Running` | imported | pulse → panel |
| `tasks.py` | `Tasks(QFrame)`: one project of one install task by task — the state line, the table in SQX's order with a bar on the running task (and full on the done ones), the log tail | imported | progress → panel |
| `running.py` | `Running(QFrame term)`: «En marcha» — one install/project picker for both halves, `Pulse` above and `Tasks` below, a line saying whether they are the same run; preselects the project a worker runs (custodian first), else the window's selected project; tasks refresh every 3 s while shown | imported | ops/sqx + progress → zone |
| `progressbar.py` | `bar(percent)`: the thin 0-100 % `QProgressBar` both views use; None runs it as a busy indicator instead of inventing a figure | imported | percent → widget |
| `ledger.py` | `Ledger(QFrame term)`: «Registro de búsquedas», one study's ledger, read-only — what it is and why it matters in a box, how many rows are the window's filters (`launched_by` «ventana», in the accent colour), blind door of step 20, pooled N and σ, and three tabs: funnel, history spent per segment, every search | imported | ledger → zone |
