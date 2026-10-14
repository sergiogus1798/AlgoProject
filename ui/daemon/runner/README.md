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
| `api.py` | The run routes of the study viewer: start a study, one sub-test beside the stored result, the screen as a page, cancel. | imported | request → JSON |
| `batch.py` | Fold N one-strategy jobs of one study into a single batch job that forks over the cores. | imported | plans → plans |
| `batchrun.py` | Run one study's per-strategy commands in one process: import once, fork a worker per core. | `python3 -m ui.daemon.runner.batchrun --plan P --workers N` (the daemon starts it) | plan → per-strategy results + log |
| `offer.py` | Which studies a strategy page can use in its own databank, and where the others live. | imported | place → `{study: {why, go}}` |
| `optimisation.py` | The command lines of the optimisation family (steps 16.5-19), or why the window cannot start one. | imported | context → argv · sentence |
| `readings.py` | The command lines of the readings and closing families and the trade Monte Carlo, or why not. | imported | context → argv · sentence |
| `rootseed.py` | The one root of a monkey run: every subprocess of it is handed the same `--seed` (encargo 66 §1.5, D2). | imported | databank → seed |
| `screening.py` | The command lines of the screening and data families (steps 4-8), or why the window cannot start one. | imported | context → argv · sentence |
| `table.py` | One press of a run button into the commands to start, or the Spanish sentence why none can start. | imported | request → argv list · sentence |
| `transfer.py` | The command lines of the transfer and breakage families (steps 9-16), or why the window cannot start one. | imported | context → argv · sentence |
| `where.py` | Where a study's input lives on the data root, found before a run is offered — never computed. | imported | data root → paths |

## Contracts and traps

- **A plan is `plan(c, strategy) -> argv | sentence`**, `c` from `runs.context`, `strategy` ""
  for the population. `scope="one"` with N strategies is N plans, one per strategy, which `batch.fold` turns into ONE batch job when N ≥ 2 and the study does not fan out itself (owner, 2026-09-28: 207 processes of ~1 s, 16 at a time, left the machine idle; one batch of 44 workers does 200 in ~9 s instead of ~43 s); `many` is one.
  Each entry says whether it has `one`, `many` and whether its command takes `--set`; a study
  the window never starts carries only `why`.
- **Some commands get `--set` from the context before the owner's overrides**: `entryQuality`
  (`run.feed`, `run.timeframe`) keeps the feed in `config.yaml`, where it would otherwise read XAUUSD for every
  project. Its `config_hash` includes these, so a drawer that hashes only the owner's overrides
  marks its results stale.
- **A cross-market export is one whose `Symbol` names more than one feed.** Every export carries
  the column since 2026-09-24; testing for the column refused every single-market study.
- **`only` never goes through a study's `report --only`**, which rewrote the full run's
  `estrategias/<S>.json` (OPEN §54). `api._rerun` starts `ui.daemon.results.rerun` per strategy,
  which calls `one.run(only=…)` and writes under `<study>/parciales/`. crossmarket offers each
  non-base market of the export; monteCarlo the «Prueba» options of the chosen strategy's newest
  stored result (`/api/study/only?strategy=`), mapped back to the sub-test label by the rerun.
- **A batch study (cloud, wfc, cscv, marketSurfaces) refuses when the mother has two batches**,
  `strategyPermutations/` and `pipeline/`: which one is the owner's call.
- **Studies that sign a ledger row under a template family** (wfc, cscv,
  marketSurfaces, blindJoint) get `--family` = the template's name in
  `AlgoData/projects/registry.csv` (owner, Q9 of plan 24): a library template is
  `<name>/template.sqx`, so the name is its folder, not the file's stem. A project with no
  template in the registry is refused with that sentence: nothing is signed under a guess.
  `--timeframe` comes from the same row.
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
