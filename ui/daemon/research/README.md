# ui/daemon/research — «Investigar»: the map, the memory, the board, the proposal and the queue of its ideas

Phase 5 of the research director (`docs/AgentPDFs/director-de-investigacion-2026-10-01.md` §6, §8).
Reads that cost nothing, and one confirmation-gated job: the queue (the fourth launcher of the window: it reaches the custodian).

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | «Investigar»: the profile's map, the memory, the director's proposal and the queue of its ideas. | imported | — |
| `api.py` | The routes of «Investigar»: the map, the memory, the board, the proposal and the queue. | imported | request → JSON |
| `explain.py` | What each profile measure and each of its columns means, one Spanish sentence each. | imported | — |
| `preflight.py` | Whether a proposal's queue may be launched now, and the sentence the owner confirms. | imported | proposal → `{ok, reasons, ideas, projects, text}` |
| `proposals.py` | The saved proposals as the window reads and changes them: the veto and the owner's answers. | imported | proposals folder → dict |
| `queue.py` | The queue of a proposal's ideas: one after another on the custodian, each through five steps. | `python3 -m ui.daemon.research.queue --proposal ID` (every project is `Research_<SYMBOL>_<template>_<TF>`) (the window queues it) | proposal → `queues/<id>.json` |
| `steps.py` | The five real steps one idea goes through: rule 5, the template, the project, the palette, the autopilot. | imported | idea → template, project, run |
| `views.py` | What the «Investigar» panel reads: the profile's map, one cell's measures, the memory, the board. | imported | profile + memory → dicts |

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
