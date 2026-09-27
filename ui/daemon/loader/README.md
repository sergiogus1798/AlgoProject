# ui/daemon/loader — a databank's data, loaded the moment the window selects it

Owner, 2026-09-27: choosing a project and databank loads its strategies' data, with no command
typed. Three pieces, each with its own lifecycle under the data root:

| piece | where it lands | how | SQX |
|---|---|---|---|
| metrics | `metrics/<P>/<D>/` (the one current export) | `sqx.export.export_metrics`, SQStats off each `.sqx` | no |
| trades | `raw/<P>/<D>/<day>/` | `export_trades`, or `export_retest` (data=all) when the files carry cross-check markets | one-shot `orderstocsv` on the conductor |
| cosecha | `harvest/<P>/<D>/<day>/` | `studies.screening.gate.harvest`, only for a build databank with an `OOS` retest | one-shot `orderstocsv` on the conductor |

A piece is **stale** when any `.sqx` it reads (or its folder, for a file removed) is newer than
its manifest. The conductor jobs run one at a time (`ui/daemon/jobs.py`, `conductor` lane) and
`bin/sqx-worker.sh run` refuses when another `sqcli` holds that install: the job fails, the piece
reads `failed` with the refusal, and it is **never queued again on its own** — the owner's ↻ does.
While SQX is writing the selected project (today's log started it and has not finished it),
nothing of it is read or queued.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The package's one-line purpose | imported | — |
| `find.py` | Where a databank lives (workers first), its `OOS` partner from the `project.cfx`, whether its files carry cross-check markets, whether SQX is writing the project, and its roster (identity → name, cached per folder state) | imported | project, databank → paths, facts |
| `state.py` | Each piece's state, the command that refreshes it and the lane, and `load()`, which queues what is missing once | imported | project, databank → status, jobs |
| `api.py` | `GET /api/load` (state only) and `POST /api/load` (queue what is missing; `retry` for what failed) | imported | request → JSON |
