# ui — the desktop application

One window, one daemon, and `core/` underneath. This is the first slice of the unified platform
described in `docs/AgentPDFs/plataforma-unificada-2026-09-20.md`. Three modules so far: the
**template library**, the **asset library** — every instrument's costs, windows and MC Retest
ranges, plus the four shared files that decide for all of them — the **strategies zone**, the
databanks as SQX groups them and, per strategy, what every analysis module already said about it —
and the **IS/OOS gate**, step 8 of the workflow: the funnel, the scorecard and the run. The remaining zones of that study
are named in the sidebar and open a page saying what will live there — they arrive as a view here,
never as a second window.

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

**It never runs SQX and it never authors anything.** The chat writes a draft brief and hands over
the prompt; the authoring is `/strategy-template`, which installs blocks into a real install and is
the conductor's lane. A window that quietly wrote to `SQX_w1` would break the lane table in
`sqx/CLAUDE.md` the first time two sessions had it open.

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
one actually missing; `docs/manual/35-app-plantillas.md` has the command that names the real one.
