# ui/daemon — the process that owns the library

FastAPI on loopback. Everything the window knows, it learns here; everything it changes, it changes
here. No Qt import belongs in this folder.

```
app ─▶ routers ─▶ templates ─▶ library ─▶ registry.csv · runs.csv · library/<name>/
 │                │           coverage · writes (sqx.templates.registry.append) · palettes
 │                │           interview ─▶ brief ─▶ AlgoData/templates/drafts/<name>.json
 │                ├─ assetapi ─▶ assets ─▶ core.assetwrite
 │                ├─ jobsapi ─▶ jobs · progress ─▶ tasklog
 │                └─ one package per surface (the table below)
 └── /api/health ─▶ version · jobs · progress
```

**Imports from:** `core/`, `sqx/templates/`, `ui/text` (labels and figures, pure Python), and
through the packages `ledger/`, `pipeline/ledger`, `sqx/projects/stage`, `sqx/curate` and each
study's config loader · **Consumed by:** `ui/desktop/` (over HTTP only), `core/archive/view.py`
(`gateview`)
**Must not contain:** a Qt widget, an SQX command outside `advance/`, or a second way of writing a
CSV. `jobs.py` starts `python3 -m` analysis modules and nothing else: never `sqcli`, never a
worker — the one route that reaches SQX is `advance/`'s «Continuar workflow», on a worker only.

| file | what it does | run it | in → out |
|---|---|---|---|
| `app.py` | The app: includes every router of `routers.py` and serves `/api/health` (code fingerprint, pid, busy jobs, which installs exist — the read-only mode) | imported | request → JSON |
| `routers.py` | `ROUTERS`, every router the daemon serves in the order `app.py` includes them; a new surface is one line appended at the end | imported | — |
| `templates.py` | The library's routes as a router: `/api/templates`, `/api/template/{name}` (+ `/status`), `/api/coverage`, `/api/verdict`, `/api/palettes`, `/api/palette/{name}` (+ `/delete`), `/api/palettes/new`, `/api/interview/step`, `/api/interview/finish` | imported | request → JSON |
| `jobsapi.py` | The routes every zone shares: `/api/jobs` (the daemon's job list), `/api/progress/installs` and `/api/progress` (where an SQX project stands, from files) | imported | request → JSON |
| `version.py` | Fingerprint of the daemon's own code, served by `/api/health` so the launcher replaces an idle daemon left over from older code | imported | files → 16 hex |
| `serve.py` | Bind to 127.0.0.1 and serve | `python3 -m ui.daemon.serve [--port P]` | — |
| `library.py` | What the library holds: registry rows, runs, and what is really on disk | imported | disk → dicts |
| `coverage.py` | The matrix of runs and the headline counts | imported | catalogue → grid |
| `writes.py` | The three writes: status, notes, verdict | imported | change → row |
| `palettes.py` | The palette library resolved against the taxonomy, and its four writes: save, create, clone, delete | imported | disk → JSON · a palette → its file |
| `assets.py` | What the asset zone draws: every instrument with what blocks it, one asset in full, and the writes it may make | imported | disk → JSON |
| `assetapi.py` | The asset library's routes, as a router | imported | request → JSON |
| `runs.py` | What running one module on one strategy means: the argv, given the asset's feed and what `raw/` and `harvest/` hold — or the sentence saying why it cannot run here; `guess_asset` reads a project's asset off its name | imported | context → argv · reason |
| `jobs.py` | The daemon's job list: commands started from the window as its own children, each logged under `AlgoData/logs/ui/`; the python lane and the one-at-a-time conductor lane | imported | argv → job record |
| `gateview.py` | A gate report read off disk: its funnel and scorecard (`gate`), one strategy's paired metrics and daily curve (`strategy`), which report judged a cosecha (`judged`), the screens as configured (`screens`) — for the databank panel's funnel and `core.archive.view` | imported | disk → JSON |
| `progress.py` | Where a running SQX project is: its tasks from `project.cfx`, which one runs and how far from the tail of today's log, and each databank's count on disk. Files, plus the worker's status line through `tasklog` | imported | disk → JSON |
| `tasklog.py` | A project's own task log — each task's start, finish, input counts and time per strategy — and the worker's `-project action=status` line while it runs | imported | disk · HTTP → dicts |
| `interview.py` | The questions the chat asks, and which is next | imported | answers → question |
| `brief.py` | A finished interview into a draft brief, a prompt and the commands | imported | answers → files |

Retired by F13 of plan 24 (2026-09-28) with the zones that alone used them: `studyapi.py` (the
first strategies zone's `/api/databanks`, `/api/databank`, `/api/results`, `/api/run` and the gate
zone's `/api/gate/*`; its job and progress routes moved to `jobsapi.py`) and `studies.py`.

The surfaces' routers, each a package with its own README, all listed in `routers.py`:

| folder | routes | what it reads |
|---|---|---|
| `results/` | `/api/catalogue`, `/api/result`, `/api/history`, `/api/config`, `/api/config/hash`, `/api/matrix`, `/api/projects` | `AlgoData/reports/<P>/<D>/<day>/<study>/` as the study contract; the catalogue's run fields come from `runner/table.py` |
| `runner/` | `POST /api/study/run`, `/api/study/only`, `POST /api/jobs/{id}/cancel` | the data root, to build each study's `python3 -m` command or say why not; queued in `jobs.py` |
| `workflow/` | `/api/workflow` | the steps of WORKFLOW.md for one project, from files, logs and the ledger |
| `ops/` | `/api/pulse`, `/api/ops/sqx`, `/api/ledger` | `/proc`, the workers' logs and `sqcli.config`, `AlgoData/ledger/*.jsonl`; a worker whose log says a project runs is asked its `action=status` line (through `progress.state`) and nothing else |
| `tearsheet/` | `/api/tearsheet`, `/api/tearsheet/exits` | the newest `harvest/<P>/<D>/<day>/{equity,trades,metrics}.parquet`, filtered on identity; IS and OOS apart, any other sample refused; `sample=OOS2` answers `{blocked}` until 17-19 are in the ledger, then from a cosecha with an oos2 sample |
| `tearmarket/` | `/api/tearsheet/market`, `/api/tearsheet/trades` | the same harvest plus the asset's bars through `core.barstore`, cut at the end of oos1 |
| `batch/` | `/api/batch`, `/api/batch/has` | a mother's `strategyPermutations/` or `pipeline/` `metrics.parquet` — only labels, `param_*`, `NetProfit (build)` and `NetProfit (oos1)`; every oos2/ALL column dropped before reading |
| `loader/` | `GET`/`POST /api/load` | a databank chosen in the window: its files on whichever install holds it, the `project.cfx` for its OOS partner, the `metrics/`, `raw/` and `harvest/` manifests; queues what is missing or stale — metrics on the python lane (no SQX), trades and cosecha on the one-at-a-time conductor lane |
| `data/` | `/api/data/catalogue`, `/api/data/assets`, `/api/data/bars`, `/api/data/spread`, `/api/data/feedquality` | the data root through `perf.disk.inventory` and its `manifest.json` files; the bar library through `core.barstore` (cached in `barsDerived/`); the step-4 contract dicts in `spread/<feed>/` and `feedQuality/<feed>/` — no export, no SQX |
| `projects/` | `/api/projects/all`, `/api/projects/find` | every project of the gallery: each install's `project.cfx`, `registry.csv`, `reports/`, the rosters for the total and today's log for the state — `-project action=status` only to a worker running it, never `count` |
| `sqxconfig/` | `/api/sqxconfig`, `POST /api/sqxconfig/value` | `assets/_build.yaml`, `_classes.yaml`, the globals of `_policy.yaml` and `_markets.yaml` (read only) through `core.assetyaml`; writes one value through `core.assetwrite.set_value`, comments kept — no SQX |
| `databank/` | `/api/databank/panels`, `/table`, `/equity`, `/funnel`, `POST /api/databank/reload` | the databank panel of Proyecto: roster (`loader.find`), `metrics/` or the cosecha, every study under `reports/<P>/*/` paired by identity, the mothers' batch studies (`estudios/`) by name, the `spread` report's trades, `gate/funnel.csv`, the ledger's door for 17-20 — no SQX; reload only asks `POST /api/load` |
| `filters/` | `/api/filters/metrics`, `POST /apply`, `POST /discard`, `POST /clear`, `/state`, `GET`/`POST /saved` | the databank table's real columns (OOS2 left out) and the stored `distribution` blocks; writes `AlgoData/filters/<P>/<D>/discards.jsonl` and `saved.yaml`, and one ledger row per filter or manual deletion through `ledger.record.log` — no `.sqx`, no SQX |
| `advance/` | `/api/advance/preflight`, `POST /api/advance/run` | `registry.csv`, the worker's port, `/proc`, its projects' dates and today's SQX log, F6's `discards.jsonl`, the project's `project.cfx`; the job copies the discards to `AlgoData/projects/discards/`, cuts through `sqx.curate.apply_verdict.apply`, stages, starts the worker, sends `-project action=start` and then only `action=status` until «Project finished», and stops it — **the one route that reaches SQX**, never the master |
| `strategy/` | `/api/strategy/meta`, `/costcurve`, `/stats`, `/archived`, `POST /api/strategy/archive` | the Estrategia page: the `.sqx` by file read (the install, else an export's copy under `raw/`, else the archive) through `sqx.inspect.strategymeta`, the cosecha and the `spread` report's trades, the ledger's door for OOS2; «Archivar» freezes through `core.archive.write` — no SQX. With `source=archive`, it and `results/`, `tearsheet/`, `tearmarket/` answer from `core.archive.read` |
| `archive/` | `/api/archive/list`, `/api/archive/show` | PORTFOLIOS: `AlgoData/archive/` through `core.archive.read` — each archived strategy with its versions, the ledger count frozen that day, and what one version holds and skipped; files only, no job, no SQX |

## Contracts and traps

- **`writes.py` never writes a CSV itself.** It calls `sqx.templates.registry.append`, the same
  function the command line calls. Two writers for one file is how a column drifts.
- **The registry is a claim; `library.folder()` is the evidence.** A row whose folder is missing is
  shown as missing rather than dropped: SQX does not error on a template whose blocks are absent,
  it removes it from the builder in silence.
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
