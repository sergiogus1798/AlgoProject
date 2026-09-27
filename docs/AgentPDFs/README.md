# docs/AgentPDFs — the owner's dossiers, and the briefs written to leave the project

Long documents that do not fit `knowhow/` (one fact per card) nor the manual (one command per
page): the plan, the design of a module, a report on a run, or a brief handed to an agent that has
never seen the code. **A dossier that has been acted on and whose facts are in `knowhow/` is
deleted, not kept "just in case"** — cleanup of 2026-09-26 removed the Monte Carlo specs and audit,
the capabilities brief, the 2026-09-22 cost report, the storage analysis, the 2026-09-25
performance summary, the execution plan and the robustness protocol of 2026-09-21 (their status
tables contradicted the code) and the 2026-09-22 review. All are in git history.

## What lives here

| file | kind | status |
|---|---|---|
| `WORKFLOW.md` | the 25 steps, dictated by the owner | **living, undated — it rules over every other file here** |
| `plataforma-unificada-2026-09-20` (+pdf) | feasibility study for one app over SQX and AlgoProject; `ui/` is its descendant | design reference of `ui/` |
| `puerta-oos-2026-09-23` | design dossier of `studies/screening/gate/` | cited by its README and config |
| `profiling-workflow-2026-09-26` | the 25 steps run end to end on USDJPY H1, with time, CPU, memory and disk | report of encargo 21 |
| `workflow-usdjpy-m30-2026-09-27` (+pdf) | the 25 steps run end to end on USDJPY M30 with the new `donchianUpperCrossUp` template, every test, and the incidents found (OPEN.md §57-§63) | report of the owner's 2026-09-26 night request; the template's reading awaits his confirmation |
| `catalogo-para-la-ui-2026-09-25` (+pdf) | outbound brief: everything the toolchain does, for whoever designs the window | inventory — goes stale |
| `paneles-flask-inventario-2026-09-25` | outbound brief: the depth of the three retired Flask panels, with the ten-point contract the «Estrategias» zone keeps | the bar for that zone |
| `respuestas-calidad-del-feed-2026-09-26` (pdf) | the owner's answers to the 16 decisions, with formulas | source of `ledger/thresholds.yaml` `feedQuality.` |
| `calidad-del-feed-decisiones-2026-09-26` (+pdf) | the 16 decisions the feed-quality module needs, each with a proposal measured on the M1 feed itself — replaces the outbound consultation | answered 2026-09-26 — the owner's answers and what the built module measured are its last section; the thresholds live in `ledger/thresholds.yaml` |

## Conventions

- Dated stem, `<topic>-YYYY-MM-DD`: the date it was written, not when the module last changed. A
  `.pdf` beside the `.md` carries the figures the `.md` cannot; regenerate it with the manual's own
  stylesheet (`tools/manual.py` holds the `STYLE`; there is no committed tool for one dossier).
- Every empirical number says which databank, export or run it came from.
- **The dossier keeps the narrative and the plan; `knowhow/` keeps the facts.** Where they disagree,
  `knowhow/` wins. Findings that outlive a dossier go to `knowhow/` in the same task.
- A design dossier closes with what was **not** verified — one that reads as certain gets built on.
- **Language follows the reader.** Owner's dossiers are in Spanish. An outbound brief is in the
  language of the conversation it walks into, and says which on its last page.

Not covered by `tools/checks.py`: these are hand-triggered deliverables, not generated on every run.
