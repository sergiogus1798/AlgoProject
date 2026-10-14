# ui/desktop/ops — OPERACIÓN: «En marcha», «Registro de búsquedas» and the jobs strip

Views only; every figure comes from the daemon (`/api/jobs`, `/api/ops/sqx`, `/api/pulse`,
`/api/progress`, `/api/ledger`). Labels through `glossary.label`, numbers through `numbers.num`.

**Imports from:** `ui/desktop/client.py`, `theme.py`, `glossary.py`, `numbers.py`,
`durations.py`, `resultspanel.py`, `selection.py` · **Consumed by:** `ui/desktop/shell.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `jobsbar.py` | The status-bar strip of jobs: what runs, a 0-100 % bar for each, what waits, and a cancel. | imported | jobs → strip |
| `ledger.py` | «Registro de búsquedas»: one study's searches, its funnel and the history it has already spent. | imported | ledger → zone |
| `progressbar.py` | One 0-100 % bar in the terminal look, shared by the jobs strip and «En marcha». | imported | percent → widget |
| `pulse.py` | The custodian's pulse inside «En marcha»: the line of a long run, its figures explained, the last readings. | imported | pulse → panel |
| `running.py` | «En marcha»: the custodian's pulse and one project's tasks — the same project, one screen. | imported | ops/sqx + progress → zone |
| `tasks.py` | One SQX project task by task, read from its install: the lower half of «En marcha». | imported | `/api/ops/steps` → panel |
