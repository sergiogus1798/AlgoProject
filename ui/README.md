# ui — the desktop application

One window, one daemon, and `core/` underneath. This is the unified platform described in
`docs/AgentPDFs/plataforma-unificada-2026-09-20.md`, redrawn by the owner on 2026-09-27
(`docs/encargos/22-ventana-rediseno.md`) and built by plan 24. It is the only window on this
machine: the older zones and the mock on invented data were deleted on 2026-09-28 (owner: «borra
la UI anterior; quiero que en esta máquina esté solo la nueva»). The sidebar holds four groups:

| group | zones | what it is for |
|---|---|---|
| BIBLIOTECA | Cobertura, Plantillas, Nueva plantilla, Paletas, Activos, Configuración SQX, Datos | what the owner builds from: the template library and its coverage, the palettes, every instrument's costs and windows, the SQX settings new projects get, the data root and the step-4 studies |
| PROYECTO | Proyectos → Proyecto → Estrategia | one project judged: the gallery of every install's projects; one project's workflow rail, funnel and databank panel (with the filters and «Continuar workflow»); one strategy's ficha — curves, IS/OOS1/OOS2 statistics, metadata, «Archivar» and every study below |
| OPERACIÓN | En marcha, Registro de búsquedas (+ the jobs strip in the status bar) | what runs: the custodian's pulse and the SQX project's tasks one by one; the ledger — one line per search that looked at data and reduced a population, the window's filters included |
| PORTFOLIOS | Portfolios | the archived strategies; «Importar» opens one on the Estrategia page as it was frozen, nothing recomputed |

Above the zones a fixed context bar reads `Proyectos › proyecto › estrategia` from
`desktop/selection.py`, the one global selection; each crumb opens its zone, the identity lives
only in the strategy crumb's tooltip. Ctrl+K anywhere opens the command palette
(`desktop/cmdpalette.py`) over zones (with aliases: «ledger»), projects, databanks, the chosen
databank's strategies and, with a strategy chosen, its studies.

**Studies are drawn by the contract, not by the study.** Every study returns the dict of
`core/study/CONTRACT.md` (tabs, selectors, block kinds, verdict, `config_hash`), so the window has
one widget per block kind (`desktop/blocks/`) and one generic page (`desktop/studypage/`) instead of
a view per study. A new study appears in Proyecto's databank panel (its columns) and in
Estrategia's study tabs the day it writes that contract under
`AlgoData/reports/<P>/<D>/<day>/<study>/` and gets a row in the daemon's catalogue
(`daemon/results/catalogue.py`), runner (`daemon/runner/`) and panel layout
(`daemon/databank/layout.py`). The daemon reads, the window paints; staleness is the study's own
`config_hash` against what today's config would sign.

```
bin/algoui ─▶ ui/desktop/launch ─▶ ui/desktop/shell ─▶ zones
                     │                                   │  HTTP, loopback only
                     └── spawns if absent ──▶ ui/daemon/serve ─▶ ui/daemon/* ─▶ core/, sqx/
                                  both sides ─▶ ui/text (labels, figures; pure Python)
```

| folder | what it holds | rule |
|---|---|---|
| `daemon/` | FastAPI on 127.0.0.1. Owns every read and every write of the library | no Qt import ever |
| `desktop/` | PySide6. Draws what the daemon says | **no view opens a file or a CSV** |
| `text/` | The glossary of visible labels and the number formatter, used by both | no Qt, no FastAPI, no file |

## The owner's decisions of 2026-09-27 (encargo 22 §0)

Each changed a rule written here before; this is where they now live.

| decision | what it means in the code |
|---|---|
| The window **may launch the next SQX task** with «Continuar workflow», always after a confirmation screen | `daemon/advance/`, the one exception in «What it does not do» below |
| PROYECTO goes from six zones to **three** | the table above; the five older zones and their files are gone (`desktop/README.md`) |
| On a machine without SQX the window is **read-only** (the Windows reading of §11, answered «Linux only» in plan 24 Q2) | `/api/health` → `sqx.installs`; `shell.guard` shows the banner and disables what reaches SQX, with the reason in the button's own text |
| **Every filter the owner applies is written in the Ledger** as a search | `daemon/filters/` writes one row per filter or manual deletion through `ledger.record.log`; Registro de búsquedas shows them |
| The WFC admits **any composition** of IS/OOS; the discipline is the owner's, and each composition read is written down | `studies/optimisation/wfc` (`build` always IS; the IS may be `build` or `build+oos1`), one ledger row per segment read |
| OOS2 appears in the ficha **only when it is available**: after steps 17, 18 and 19 | `/api/strategy/stats` and `/api/tearsheet` answer `{blocked}` until the ledger's door opens; step 20's panel is listed and locked |

## Why two processes and not one

The study's decision, taken on the day this was built rather than after: the moment a view has to
show a running SQX build, the thing that runs it cannot be the thing that paints. Splitting later
means rewriting every view; splitting now costs one HTTP hop that nobody can measure. The daemon
also survives the window — close it, reopen it, the job is still there.

The daemon binds loopback and only loopback. It can rewrite `registry.csv`, `runs.csv` and
everything under `assets/`, so it is not something to put on the network of a machine that also
runs three SQX installs.

## What it does not do

**It never authors anything, and it drives SQX for two things only.** The chat writes a draft
brief and hands over the prompt; the authoring is `/sqx-strategy-template`, which installs blocks
into a real install and is the conductor's lane. A window that quietly wrote to `SQX_w1` would
break the lane table in `sqx/CLAUDE.md` the first time two sessions had it open.

The two exceptions, both the owner's (2026-09-27):

- **Choosing a databank loads it** (`daemon/loader/`, `desktop/loadbar.py`). Its metrics and
  curves are read off the `.sqx` with no SQX at all (`core/sqxview.py`); only the trades need a
  JVM, `orderstocsv` — a one-shot `sqcli` on the conductor through `bin/sqx-worker.sh run`, which
  refuses when another `sqcli` holds that install. Never a start or a stop of an install, never a
  project written, never a failed load retried on its own. While SQX is writing the selected
  project, nothing of it is read.
- **«Continuar workflow» launches the next SQX task, after a confirmation screen, on a worker
  only** (`daemon/advance/`, `desktop/workspace/advance.py`). The owner's filters live in
  `AlgoData/filters/` and touch nothing in SQX; the button turns them into a `/curate`
  (`sqx.curate.apply_verdict.apply`, the discarded `.sqx` copied to
  `AlgoData/projects/discards/` first), switches on only the next task (`sqx.projects.stage`),
  starts the worker (`core.worker.start`), sends `-project action=start`, then only
  `-project action=status` until «Project finished», and stops the worker it started. The
  preflight refuses the master always, a worker already up (never stopped: OPEN §32), a worker
  another project touched in the last 24 h, and a project with nothing to cut.

**The daemon's lanes** (`daemon/jobs.py`): every job is a child of the daemon, in memory, logged
under `AlgoData/logs/ui/`. The **python** lane runs analysis modules (`python3 -m studies…`)
within a core budget — a fan-out study takes half the cores, a light one three — and starts
nothing new below 20 GB of free RAM unless the lane is empty. The **conductor** lane runs one job
at a time: the loader's `orderstocsv` exports and «Continuar workflow». Nothing else reaches an
install.

The asset zone and Configuración SQX are the same rule from the other side: they write `assets/`,
which is configuration in the repository, through `core.assetwrite`, and reach no install for
anything. `instrument` and `sqx_now` are facts `sqx.inspect.instruments` refreshes — not values the
window goes and fetches, which would make opening a list a job that can block on a busy master.

## Run it

```bash
bin/algoui                      # the app (the desktop icon runs this)
bin/algoui --zone Proyectos     # open on a zone
QT_QPA_PLATFORM=offscreen bin/algoui --port 8757 --shot DIR --zone Datos   # a shot on a scratch daemon
python3 -m ui.daemon.serve      # just the daemon, to see its errors
QT_QPA_PLATFORM=offscreen python3 tools/uiwalk.py --port P   # dev: every zone against a daemon, 0 exceptions expected
```

Port: `ui_port` in `config/machine.yaml`, 8765 by default.

Qt's `xcb` plugin needs four XCB libraries Ubuntu does not ship installed, and `sudo` asks for a
password on this machine — so they live extracted in `~/.local/lib/qt-xcb/` and `bin/algoui` puts
that folder on `LD_LIBRARY_PATH` itself. Qt's own error message blames a different library than the
one actually missing; `docs/manual/02-la-ventana.pdf` (cap. 35-app-plantillas) has the command that names the real one.
