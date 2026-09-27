# ui/daemon — the process that owns the library

FastAPI on loopback. Everything the window knows, it learns here; everything it changes, it changes
here. No Qt import belongs in this folder.

```
app ─▶ library ─▶ registry.csv · runs.csv · library/<name>/
 │     coverage ─▶ the matrix and the headline counts
 │     writes   ─▶ sqx.templates.registry.append   (the CSVs have one writer, and it is not us)
 └──   interview ─▶ brief ─▶ AlgoData/templates/drafts/<name>.json
```

**Imports from:** `core/`, `sqx/templates/`, and through the packages `ledger/`, `pipeline/ledger`, `sqx/projects/stage` and each study's config loader · **Consumed by:** `ui/desktop/`
**Must not contain:** a Qt widget, an SQX command, or a second way of writing a CSV. `jobs.py` starts
`python3 -m` analysis modules and nothing else: never `sqcli`, never a worker.

| file | what it does | run it | in → out |
|---|---|---|---|
| `app.py` | The routes. One per question the window asks; every other surface is a router it includes (assets, the older studies/gate zones, results, runner, workflow, ops) | imported | request → JSON |
| `version.py` | Fingerprint of the daemon's own code, served by `/api/health` so the launcher replaces an idle daemon left over from older code | imported | files → 16 hex |
| `serve.py` | Bind to 127.0.0.1 and serve | `python3 -m ui.daemon.serve` | — |
| `library.py` | What the library holds: registry rows, runs, and what is really on disk | imported | disk → dicts |
| `coverage.py` | The matrix of runs and the headline counts | imported | catalogue → grid |
| `writes.py` | The three writes: status, notes, verdict | imported | change → row |
| `palettes.py` | The palette library resolved against the taxonomy, and its four writes: save, create, clone, delete | imported | disk → JSON · a palette → its file |
| `assets.py` | What the asset zone draws: every instrument with what blocks it, one asset in full, and the writes it may make | imported | disk → JSON |
| `studies.py` | What the data root holds per databank — the `metrics/` exports and the `harvest/` cosechas — and everything every module's reports already said about one strategy | imported | disk → JSON |
| `runs.py` | What running one module on one strategy means: the argv, given the asset's feed and what `raw/` and `harvest/` hold — or the sentence saying why it cannot run here | imported | context → argv · reason |
| `jobs.py` | The daemon's job list: commands started from the window as its own children, each logged under `AlgoData/logs/ui/` | imported | argv → job record |
| `gateview.py` | What the gate zone draws: every cosecha with its newest judgement, one report's funnel and scorecard, one strategy's paired metrics and daily curve | imported | disk → JSON |
| `progress.py` | Where a running SQX project is: its tasks from `project.cfx`, which one runs and how far from the tail of today's log, and each databank's count on disk. Files, plus the worker's status line through `tasklog` | imported | disk → JSON |
| `tasklog.py` | A project's own task log — each task's start, finish, input counts and time per strategy — and the worker's `-project action=status` line while it runs | imported | disk · HTTP → dicts |
| `studyapi.py` | The routes of the strategies and gate zones, and the job routes they share | imported | request → JSON |
| `assetapi.py` | The asset library's routes, as a router. They would double `app.py`, and a zone is not a reason for a second daemon | imported | request → JSON |
| `interview.py` | The questions the chat asks, and which is next | imported | answers → question |
| `brief.py` | A finished interview into a draft brief, a prompt and the commands | imported | answers → files |

The study viewer's routers, each a package with its own README, all included by `app.py`:

| folder | routes | what it reads |
|---|---|---|
| `results/` | `/api/catalogue`, `/api/result`, `/api/history`, `/api/config`, `/api/config/hash`, `/api/matrix`, `/api/projects` | `AlgoData/reports/<P>/<D>/<day>/<study>/` as the study contract; the catalogue's run fields come from `runner/table.py` |
| `runner/` | `POST /api/study/run`, `/api/study/only`, `POST /api/jobs/{id}/cancel` | the data root, to build each study's `python3 -m` command or say why not; queued in `jobs.py` |
| `workflow/` | `/api/workflow` | the steps of WORKFLOW.md for one project, from files, logs and the ledger |
| `ops/` | `/api/pulse`, `/api/ledger` | `/proc`, the custodian's log and `sqcli.config`, `AlgoData/ledger/*.jsonl` — no command to any install |
| `tearsheet/` | `/api/tearsheet`, `/api/tearsheet/exits` | the newest `harvest/<P>/<D>/<day>/{equity,trades,metrics}.parquet`, filtered on identity; IS and OOS apart, any other sample refused |
| `tearmarket/` | `/api/tearsheet/market`, `/api/tearsheet/trades` | the same harvest plus the asset's bars through `core.barstore`, cut at the end of oos1 |
| `batch/` | `/api/batch`, `/api/batch/has` | a mother's `strategyPermutations/` or `pipeline/` `metrics.parquet` — only labels, `param_*`, `NetProfit (build)` and `NetProfit (oos1)`; every oos2/ALL column dropped before reading |
| `loader/` | `GET`/`POST /api/load` | a databank chosen in the window: its files on whichever install holds it, the `project.cfx` for its OOS partner, the `metrics/`, `raw/` and `harvest/` manifests; queues what is missing or stale — metrics on the python lane (no SQX), trades and cosecha on the one-at-a-time conductor lane |

## Contracts and traps

- **`writes.py` never writes a CSV itself.** It calls `sqx.templates.registry.append`, the same
  function the command line calls. Two writers for one file is how a column drifts.
- **The registry is a claim; `library.folder()` is the evidence.** A row whose folder is missing is
  shown as missing rather than dropped: SQX does not error on a template whose blocks are absent,
  it removes it from the builder in silence.
- **`studies.py` finds a module's verdict by one convention, not by knowing the module.** Every
  report CSV that speaks per strategy names it in a `strategy` column (`Strategy Name` in the
  exports; `decay` wrote `name` until 2026-09-25). The zone reads any CSV under `reports/<project>/` with such a
  column and shows the matching row, so a new module appears in the window the day it writes
  that column — and a module that names the strategy some other way is invisible there.
- **`runs.py` refuses before starting, never after.** A module's inputs are checked against the
  data root — a trades export, a cosecha, whether the export is cross-market — and a missing one
  comes back as the sentence the window shows instead of a button. A job that fails anyway shows
  the end of its log in the same place; the log stays under `logs/ui/`.
- **A project's asset is read off its name.** Exports do not record the feed, so
  `runs.guess_asset` takes the longest asset symbol the project name contains and the window
  lets the owner override it. A project named without its asset gets no button until one is
  chosen.
- **A gate report is tied to its harvest by the manifest, not by the folder date.** The report
  is dated the day it ran; `gateview.judged` reads `source.harvest` to find the newest report
  over a harvest, so a harvest judged twice shows its latest judgement.
- **`tasklog.status` is the one command the custodian may receive mid-job** (`-project
  action=status`, owner 2026-09-25): it syncs nothing. It is asked only while the install log
  says that project runs, and never of the master. Everything else in the zone is files.
- **`progress.py` never talks to an install.** The tail of `user/log/StrategyQuant/log_<hoy>.log`
  gives the task boundaries and the percentage (in the compute thread's name); `project.cfx`
  gives the tasks and which are active; the databank folders give counts. Route B of the
  platform study: works with the master's GUI up and with the custodian mid-job, which a
  `-databank action=count` would not (the custodian takes no command while it runs).
- **Jobs live in memory.** They are children of this daemon; when it dies they die, and a record
  that outlived them would describe processes that do not exist.
- **The interview is stateless.** The whole conversation is the answers dict the client holds, so a
  window closed halfway loses nothing the daemon was keeping.
- **`assets.py` never parses or writes a YAML itself.** It calls `core.assetwrite`, the same
  module the command line would. The four shared files and the nineteen symbol ones have one
  writer, and a second one is how a comment gets lost.
- **Two answers have no default and never will**: the idea, and state-versus-transition. Skipping
  either raises here instead of guessing — they are different strategies, not spellings.
