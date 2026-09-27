# ui/daemon/runner — the run side of the study viewer

One press of ▶ (this strategy), ▶▶ (the whole population) or ↻ (one sub-test alone) becomes the
`python3 -m studies.<family>.<study>.report …` command(s) that study really takes, queued in
`ui/daemon/jobs.py` — or the Spanish sentence the window shows instead of a button.

**Imports from:** `core/`, `pipeline.ledger.state`, `ui/daemon/runs.py`, `ui/daemon/jobs.py` ·
**Consumed by:** `ui/daemon/app.py` (`ROUTER`) · **Must not contain:** an SQX command, a study's
maths, or a write anywhere but a job's log. Every command here reads files; none reaches an
install over HTTP or starts one.

| file | what it does | run it | in → out |
|---|---|---|---|
| `api.py` | The routes: `POST /api/study/run`, `GET /api/study/only`, `POST /api/jobs/{id}/cancel` | imported | request → JSON |
| `table.py` | Every study's entry, merged; one request into its jobs, or the reason none can start | imported | request → argv list · sentence |
| `screening.py` | The command lines of steps 4-8: gate, isOos, filters, decay, monkeyExcess, feedQuality, and why the rest cannot start | imported | context → argv · sentence |
| `transfer.py` | The command lines of steps 9-16: crossmarket, crossTF, mcRetest, spp; crossmarket's per-market sub-tests | imported | context → argv · sentence |
| `optimisation.py` | The command lines of steps 16.5-19: cloud, wfc, cscv over a mother's batch, and wfm | imported | context → argv · sentence |
| `readings.py` | The command lines of readings, closing and the trade Monte Carlo | imported | context → argv · sentence |
| `where.py` | Where an input lives: newest dated folder, an export's markets and timeframe, a mother's batch, the crossTF fabrication | imported | data root → paths |

## Contracts and traps

- **A plan is `plan(c, strategy) -> argv | sentence`**, `c` from `runs.context`, `strategy` ""
  for the population. `scope="one"` with N strategies is N jobs, one per strategy; `many` is one.
  Each entry says whether it has `one`, `many` and whether its command takes `--set`; a study
  the window never starts carries only `why`.
- **Some commands get `--set` from the context before the owner's overrides**: `entryQuality`
  (`run.feed`, `run.timeframe`) and `conditionalMap` (`run.symbol`, `run.feed`,
  `run.timeframe`) keep the feed in `config.yaml`, where it would otherwise read XAUUSD for every
  project. Their `config_hash` includes these, so a drawer that hashes only the owner's overrides
  marks their results stale.
- **A cross-market export is one whose `Symbol` names more than one feed.** Every export carries
  the column since 2026-09-24; testing for the column refused every single-market study.
- **`only` exists for crossmarket alone** (`--strategy` + `--only <feed>`). monteCarlo's
  `one.run(only=...)` can re-run one sub-test, but its `report.py` has neither `--strategy` nor
  `--only`, so the window cannot ask for it.
- **A batch study (cloud, wfc, cscv) refuses when the mother has two batches**,
  `strategyPermutations/` and `pipeline/`: which one is the owner's call.
- **Studies that sign a ledger row under a template family** (snoopingScreen, marketSurfaces,
  blindJoint) never start here: the window does not know the family, and a wrong one charges
  the look to another study. atrCalculator does start: its family defaults to the project.
- **The queue lives in `jobs.py`**: jobs share a budget of `SLOTS` = the physical cores; a study
  that fans out itself (`WIDE`) weighs half of it, a light one `LIGHT` = 3 (sixteen at once), and
  nothing new starts under `FLOOR_GB` free RAM while something runs; the rest wait `queued` in the
  order pressed; a finished job starts the next from its own watcher thread. Cancel kills the
  whole process tree (psutil), because the studies fan out with multiprocessing. `lane` is
  always `python`: the window starts nothing on the conductor or the custodian.
