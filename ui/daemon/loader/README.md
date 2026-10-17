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
| `__init__.py` | Loads a databank the window selects: what it lacks, what is stale, and the jobs that fetch it. | imported | — |
| `afterrun.py` | Export every new or stale databank of an install's custom projects, right after it stops. | `python3 -m ui.daemon.loader.afterrun --role custodian` | install → metrics/, raw/, harvest/ |
| `api.py` | The routes that load a databank's data when the window selects it. | imported | request → JSON |
| `extrasdef.py` | The exports an analysis reads that are not loader pieces: which databanks feed each, and the command. | imported by `afterrun.py` | — |
| `find.py` | Where a databank's files live, which retest pairs with it, and whether SQX is writing it now. | imported | project, databank → paths, facts |
| `state.py` | What of a databank is loaded, what is stale, and the commands that bring it up to date. | imported | project, databank → status, jobs |
