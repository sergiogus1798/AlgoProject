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
| `find.py` | Where a databank lives (workers first), its `OOS` partner from the `project.cfx`, whether its files carry cross-check markets, whether SQX is writing the project, and its roster (identity → name, cached per folder state; `forget()` drops the cache for «Recargar databank») | imported | project, databank → paths, facts |
| `extrasdef.py` | `EXTRA` and `SMOKE_SHARE`: the exports an analysis reads that are not loader pieces (MC ingest, SPP IS/OOS, WFM), their source databanks, marker and command | imported by `afterrun.py` | — |
| `fingerprint.py` | `fingerprint(sources)`: the .sqx files of a databank reduced to one signature that ignores SQX's resave order (read on every core from 20 files up); `state.age` compares it to the export's `.sources.sig` | imported by `state.py` | .sqx files → hex digest |
| `state.py` | Each piece's state, the command that refreshes it and the lane, and `load()`, which queues what is missing once | imported | project, databank → status, jobs |
| `afterrun.py` | (exits 1 when a piece failed: `liverun.export` runs it with check=True, `sqx-worker.sh stop` ignores it) Owner, 2026-09-28: every SQX run exported the moment it ends — but the WFC batch and its three legs (`skipped`: the variant factory harvests and empties them per mother). `bin/sqx-worker.sh stop` calls it once the process is gone (skipped with `ALGO_NO_EXPORT=1`, which `core.worker.stop(export=False)`, `core.exportdrv` and a cancel set); for every `Test_`/`Trade_` project of the install, each databank with strategies, it runs `state.commands` — metrics, trades, cosecha — one after another. While it runs, `find.AFTERRUN/<role>.pid` makes `find.writing` true for that install, so the window does not ask the same `orderstocsv` One process: the pieces run in-process (`afterrun.piece`, `runpy`), sharing `state.SEEN`. One `orderstocsv` pass: a stale build harvest runs first with `--exports` (`state.commands`: when either side's trades are stale, never for cross-market databanks; `state.load` only when `state.covers` says it pairs every strategy) and writes both databanks' trade exports, lineage included; the trades piece is asked again and skipped when fresh (`chain.load` the same). `--databank X` (repeatable) exports only the step's outputs and the build whose retest one is (`liverun.export`); the rest stays stale for the stop's export. | `python3 -m ui.daemon.loader.afterrun --role custodian` | install → metrics/, raw/, harvest/ |
| `api.py` | `GET /api/load` (state only) and `POST /api/load` (queue what is missing; `retry` for what failed) | imported | request → JSON |
