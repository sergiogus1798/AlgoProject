# ui — the desktop application

One window, one daemon, and `core/` underneath. This is the unified platform described in
`docs/AgentPDFs/plataforma-unificada-2026-09-20.md`. The sidebar holds four groups:

| group | zones | what it is for |
|---|---|---|
| BIBLIOTECA | Cobertura, Plantillas, Nueva plantilla, Paletas, Activos, Datos | what the owner builds from: the template library, the palettes, every instrument's costs and windows |
| PROYECTO | Workflow, Población, Estudio de población, Estrategia, Estrategias, Puerta IS/OOS | one project judged: the 21 steps, the strategies × studies matrix, one study of the population or of one strategy |
| OPERACIÓN | Custodio, Ledger, Generación (+ the jobs strip in the status bar) | what runs: the custodian's pulse, the search ledger, the SQX project task by task, the window's own jobs |
| CARTERAS | Carteras | reserved: a page saying what will live there |

Above the zones a fixed context bar reads `Proyecto › Población › Estrategia (identidad)` from
`desktop/selection.py`, the one global selection; each crumb opens its zone.
Ctrl+K anywhere opens the command palette (`desktop/cmdpalette.py`) over zones, projects,
databanks, strategies and studies.

Estrategia opens on the **Ficha** (`desktop/studypage/ficha.py`), which is not a study: arithmetic
on the newest harvest, IS beside OOS, in five sub-tabs — IS/OOS, Salidas, Contra el subyacente,
Operaciones and, for the mother of a variant batch only, Lote (`daemon/tearsheet/`,
`daemon/tearmarket/`, `daemon/batch/`). None of them reads or returns oos2: harvests are refused
outside IS/OOS, bars are cut at the end of oos1 and the batch's oos2/ALL columns are never read.

**The study viewer is driven by the contract, not by the study.** Every study returns the dict of
`core/study/CONTRACT.md` (tabs, selectors, eight block kinds, verdict, `config_hash`), so the window
has eight widgets (`desktop/blocks/`) and one generic page (`desktop/studypage/`) instead of a view
per study. A new study appears in Población, Estrategia and Estudio de población the day it writes
that contract under `AlgoData/reports/<P>/<D>/<day>/<study>/` and gets a row in the daemon's
catalogue (`daemon/results/catalogue.py`) and runner (`daemon/runner/`). The daemon reads, the
window paints; staleness is the study's own `config_hash` against what today's config would sign.

Estrategias, Puerta IS/OOS and Generación are the older zones, kept: each still shows something
the viewer does not (the metric table, the paired equity curve, SQX's task list) — see
`desktop/README.md`. Datos and Carteras open a page saying what will live there and how the job
is done today — they arrive as a view here, never as a second window.

```
bin/algoui ─▶ ui/desktop/launch ─▶ ui/desktop/shell ─▶ views
                     │                                   │  HTTP, loopback only
                     └── spawns if absent ──▶ ui/daemon/serve ─▶ ui/daemon/* ─▶ core/, sqx/
```

| folder | what it holds | rule |
|---|---|---|
| `daemon/` | FastAPI on 127.0.0.1. Owns every read and every write of the library | no Qt import ever |
| `desktop/` | PySide6. Draws what the daemon says | **no view opens a file or a CSV** |

## Why two processes and not one

The study's decision, taken on the day this was built rather than after: the moment a view has to
show a running SQX build, the thing that runs it cannot be the thing that paints. Splitting later
means rewriting every view; splitting now costs one HTTP hop that nobody can measure. The daemon
also survives the window — close it, reopen it, the job is still there.

The daemon binds loopback and only loopback. It can rewrite `registry.csv`, `runs.csv` and
everything under `assets/`, so it is not something to put on the network of a machine that also
runs three SQX installs.

## What it does not do

**It never authors anything, and it drives SQX for one thing only.** The chat writes a draft brief
and hands over the prompt; the authoring is `/sqx-strategy-template`, which installs blocks into a
real install and is the conductor's lane. A window that quietly wrote to `SQX_w1` would break the
lane table in `sqx/CLAUDE.md` the first time two sessions had it open.

The one exception (owner, 2026-09-27): **choosing a databank loads it** (`daemon/loader/`,
`desktop/loadbar.py`). Its metrics and curves are read off the `.sqx` with no SQX at all
(`core/sqxview.py`); only the trades need a JVM, `orderstocsv` — a one-shot `sqcli` on the
conductor through `bin/sqx-worker.sh run`, which refuses when another `sqcli` holds that install.
The daemon runs one such job at a time (the `conductor` lane of `daemon/jobs.py`), never starts or
stops an install, never writes a project, and never retries a failed load on its own. While SQX is
writing the selected project, nothing of it is read.

The asset zone is the same rule from the other side: it writes `assets/`, which is configuration in
the repository, and reaches no install for anything. `instrument` and `sqx_now` are facts
`sqx.inspect.instruments` refreshes — not values the window goes and fetches, which would make
opening a list a job that can block on a busy master.

## Run it

```bash
bin/algoui                      # the app
python3 -m ui.daemon.serve      # just the daemon, to see its errors
```

Port: `ui_port` in `config/machine.yaml`, 8765 by default.

Qt's `xcb` plugin needs four XCB libraries Ubuntu does not ship installed, and `sudo` asks for a
password on this machine — so they live extracted in `~/.local/lib/qt-xcb/` and `bin/algoui` puts
that folder on `LD_LIBRARY_PATH` itself. Qt's own error message blames a different library than the
one actually missing; `docs/manual/02-la-ventana.pdf` (cap. 35-app-plantillas) has the command that names the real one.
