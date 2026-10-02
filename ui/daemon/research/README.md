# ui/daemon/research — «Investigar»: the map, the memory, the director and the queue of its ideas

Phase 5 of the research director (`docs/AgentPDFs/director-de-investigacion-2026-10-01.md` §6, §8).
Four reads that cost nothing, and two confirmation-gated jobs: the director (tokens, no SQX) and
the queue (the fourth launcher of the window: it reaches the custodian).

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The package's one-line purpose | imported | — |
| `explain.py` | One Spanish sentence per profile measure, per column and per context figure; the three discrete intensity levels of the map | imported | — |
| `views.py` | `profile_map()`, `cell(symbol, timeframe)`, `memory()`, `board()` — JSON-safe | imported | profile + memory → dicts |
| `proposals.py` | `latest(id)` with `launchable` per idea, `veto`, `answer` (both rewrite the `.json` and `.md`), `state()` the director's step | imported | proposals folder → dict |
| `direct.py` | «Proponer investigación»: `/research-direct` headless through `CLAUDE_BIN -p`; exit 2 without a `PROPUESTA:` line | `python3 -m ui.daemon.research.direct` (the window queues it) | board → a proposal |
| `preflight.py` | `check(id)`: a launchable idea, no project of that name alive, Claude present, `advance.busy("custodian")`, `launch.api.queued()`; `text`, the sentence to confirm | imported | proposal → `{ok, reasons, ideas, projects, text}` |
| `steps.py` | The five real steps on one idea — `core.assets`, `templateArchitect`, `sqx.projects.builder --workflow`, `buildingBlocksExpert`, `pipeline.autopilot.run` then `memory.report --close` — and `Failed` / `Question` | imported | idea → template, project, run |
| `queue.py` | `run(p, runners, save)`: launchable ideas one after another, state saved after every step; a `Question` sets its idea aside, a `Failed` halts the queue | `python3 -m ui.daemon.research.queue --proposal ID` (every project is `Research_<SYMBOL>_<template>_<TF>`) (the window queues it) | proposal → `queues/<id>.json` |
| `api.py` | `GET /api/research/map`, `/cell`, `/memory`, `/board`, `/direct`, `/proposal`, `/launch`, `/queue`; `POST /direct`, `/veto`, `/answer`, `/launch` | imported | request → JSON |

**Imports from:** `studies/research/board`, `studies/research/memory`, `ui/daemon/jobs`,
`ui/daemon/advance/preflight`, `ui/daemon/launch/api` · **Consumed by:** `ui/desktop/research/`
(over HTTP), the `/research-direct` skill (`proposals.answer`).

## Traps

- **The queue's job is labelled `launch`**: that is what makes the other three launchers refuse
  while it runs (`launch.api.queued`) and what makes a cancel send SIGTERM first (`winddown`).
  `steps.terminate` passes the SIGTERM to the running child and waits for it, so the autopilot's
  own `finally` stops the custodian. The daemon itself stops no worker here: the marker carries
  the autopilot's PID, not the queue's.
- **The steps are sequential per idea**, not «three templates while the first build runs» (the
  dossier's optimisation): one job, one lane, nothing to interleave. Second and later ideas pass
  `--own-log` to the autopilot — the log of the last 15 minutes is this queue's own.
- **`templateArchitect` may rename the template**: it ends with `PLANTILLA: <name>`, and the
  project is named after that, not after the idea.
- **The autopilot does not close the memory's row itself** (`pipeline/autopilot/` was not to be
  edited): `steps.autopilot` calls `studies.research.memory.report --close` on the newest run
  folder, also after a failure.
- **Never tested against a real worker or a real Claude** (owner's authorisation pending):
  `tests/test_ui_research.py` runs `queue.run` with five fakes.
