# ui/desktop/ops — the operation zone: jobs strip, custodian pulse, ledger

Views only; every figure comes from the daemon (`/api/jobs`, `/api/pulse`, `/api/ledger`).

**Imports from:** `ui/desktop/client.py`, `ui/desktop/theme.py` · **Consumed by:** `ui/desktop/shell.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `jobsbar.py` | `JobsBar(QWidget)`: status-bar strip polling `/api/jobs` every 2 s — running jobs with percent and state, queued ones with their position, a ✕ per job (`POST /api/jobs/{id}/cancel`), failures counted. Tolerates a daemon without `percent`/`state`/`queued` | imported | jobs → strip |
| `pulse.py` | `Pulse(QFrame term)`: the custodian's one-line pulse, its figures each with a tooltip saying where it comes from, warnings in red, and the last 30 readings (in memory). Polls every 60 s only while shown | imported | pulse → zone |
| `ledger.py` | `Ledger(QFrame term)`: one study's ledger, read-only — blind door of step 20, pooled N and σ, and three tabs: funnel, history spent per segment, every search | imported | ledger → zone |
