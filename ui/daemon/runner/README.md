# ui/daemon/runner — the run side of the study viewer

One press of ▶ (this strategy), ▶▶ (the whole population) or ↻ (one sub-test alone) becomes the
`python3 -m studies.<family>.<study>.report …` command(s) that study really takes, queued in
`ui/daemon/jobs.py` — or the Spanish sentence the window shows instead of a button.

**Imports from:** `core/`, `pipeline.ledger.state`, `sqx.projects.registry`, `ui/daemon/runs.py`,
`ui/daemon/jobs.py`, `ui/daemon/databank/layout.py`, `ui/daemon/results/catalogue.py` · **Consumed by:** `ui/daemon/routers.py` (`ROUTER`), `ui/daemon/workflow/run.py` · **Must not contain:** an SQX command, a study's
maths, or a write anywhere but a job's log — save `POST /api/study/screen`, which writes the page the window asked for. Every command here reads files; none reaches an
install over HTTP or starts one.

| file | what it does | run it | in → out |
|---|---|---|---|
| `api.py` | The routes: `POST /api/study/run` (with `only`: the `ui.daemon.results.rerun` jobs), `GET /api/study/only`, `GET /api/study/offer`, `POST /api/study/screen` (the screen as a page in `<study>/pantalla/`), `POST /api/jobs/{id}/cancel` | imported | request → JSON |
| `batch.py` | `fold(planned)`: two or more one-strategy plans of one study that does not fan out itself (`jobs.WIDE`) become ONE plan running `batchrun`, its JSON under `AlgoData/logs/ui/batches/`, `weight` = `workers(n)` — physical cores − RESERVE (4), fewer when the free RAM above `jobs.FLOOR_GB` does not hold 0.6 GB each | imported | plans → plans |
| `batchrun.py` | The batch itself: `nice 10`, one BLAS thread, imports each study once, forks `workers` processes (`core.fanout`), runs each strategy's `-m` command in one of them through `runpy` into `batches/<plan>/NNNN.log`, prints `PROGRESS` per strategy and the tail of each failure; exit 1 only when every strategy failed | `python3 -m ui.daemon.runner.batchrun --plan P --workers N` (the daemon starts it) | plan → per-strategy results + log |
| `offer.py` | `offer(project, databank, strategy, asset)`: every study the runner refuses here for this strategy, its sentence, and `go` — the databank its Databanks tab reads (`layout.TABS`) when that one holds exactly one strategy of the same name, else why not (absent, a name collision, or the databank unreadable: on no install or SQX writing it). ~1.2 s, so the window asks it off the GUI thread | imported | place → `{study: {why, go}}` |
| `table.py` | Every study's entry, merged; one request into its jobs, or the reason none can start | imported | request → argv list · sentence |
| `screening.py` | The command lines of steps 4-8: gate, isOos, filters, decay, monkeyExcess, feedQuality, spread, snoopingScreen, and why the rest cannot start | imported | context → argv · sentence |
| `transfer.py` | The command lines of steps 9-16: crossmarket, crossTF, mcRetest, spp; crossmarket's per-market sub-tests | imported | context → argv · sentence |
| `optimisation.py` | The command lines of steps 16.5-19: cloud, wfc, cscv, marketSurfaces over a mother's batch, and wfm | imported | context → argv · sentence |
| `readings.py` | The command lines of readings, closing (blindJoint included) and the trade Monte Carlo | imported | context → argv · sentence |
| `where.py` | Where an input lives: newest dated folder, an export's markets and timeframe, a mother's batch, the crossTF fabrication, the project's registry row and template family | imported | data root → paths |

## Contracts and traps

- **A plan is `plan(c, strategy) -> argv | sentence`**, `c` from `runs.context`, `strategy` ""
  for the population. `scope="one"` with N strategies is N plans, one per strategy, which `batch.fold` turns into ONE batch job when N ≥ 2 and the study does not fan out itself (owner, 2026-09-28: 207 processes of ~1 s, 16 at a time, left the machine idle; one batch of 44 workers does 200 in ~9 s instead of ~43 s); `many` is one.
  Each entry says whether it has `one`, `many` and whether its command takes `--set`; a study
  the window never starts carries only `why`.
- **Some commands get `--set` from the context before the owner's overrides**: `entryQuality`
  (`run.feed`, `run.timeframe`) and `conditionalMap` (`run.symbol`, `run.feed`,
  `run.timeframe`) keep the feed in `config.yaml`, where it would otherwise read XAUUSD for every
  project. Their `config_hash` includes these, so a drawer that hashes only the owner's overrides
  marks their results stale.
- **A cross-market export is one whose `Symbol` names more than one feed.** Every export carries
  the column since 2026-09-24; testing for the column refused every single-market study.
- **`only` never goes through a study's `report --only`**, which rewrote the full run's
  `estrategias/<S>.json` (OPEN §54). `api._rerun` starts `ui.daemon.results.rerun` per strategy,
  which calls `one.run(only=…)` and writes under `<study>/parciales/`. crossmarket offers each
  non-base market of the export; monteCarlo the «Prueba» options of the chosen strategy's newest
  stored result (`/api/study/only?strategy=`), mapped back to the sub-test label by the rerun.
- **A batch study (cloud, wfc, cscv, marketSurfaces) refuses when the mother has two batches**,
  `strategyPermutations/` and `pipeline/`: which one is the owner's call.
- **Studies that sign a ledger row under a template family** (snoopingScreen, wfc, cscv,
  marketSurfaces, blindJoint) get `--family` = the template's name in
  `AlgoData/projects/registry.csv` (owner, Q9 of plan 24): a library template is
  `<name>/template.sqx`, so the name is its folder, not the file's stem. A project with no
  template in the registry is refused with that sentence: nothing is signed under a guess.
  `--timeframe` comes from the same row. atrCalculator's family defaults to the project.
- **isOos has no `--strategy`.** It reads the metrics export, the newest cosecha, or both; `one`
  with N strategies is one job, because `table.jobs` folds identical commands.
- **blindJoint** is started only after the rail's own check of the ledger's door, and its
  report asks the door again (`inputs.blind_door`).
- **The queue lives in `jobs.py`**: jobs share a budget of `SLOTS` = the physical cores; a study
  that fans out itself (`WIDE`) weighs half of it, a light one `LIGHT` = 3 (sixteen at once), and
  nothing new starts under `FLOOR_GB` = 20 GB free RAM while something runs — the owner's Python
  reserve in `knowhow/perf/ram-budget.md`; the rest wait `queued` in the order pressed; a
  finished job starts the next from its own watcher thread. Cancel kills the whole process tree
  (psutil), because the studies fan out with multiprocessing. **Two lanes**: `python`, where
  everything this runner plans goes, and `conductor`, one job at a time, used by the loader
  (`ui/daemon/loader/`) for the one-shot `orderstocsv` export — `sqx-worker.sh` refuses a second
  `sqcli` on one install. Nothing here starts a job on the conductor or the custodian.
