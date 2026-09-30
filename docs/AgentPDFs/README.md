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
| `spread-real-2026-09-27` (+pdf) | the owner's study of Darwinex's real spread: objectives, method, results and conclusions — XAUUSD, USDJPY and the five index CFDs, the spread band against price for the MC Retest, the repricing of harvests, the `%` commission charged once | **applied to the indices** (segments, spread per segment, slippage = half); XAUUSD/USDJPY proposal pending; source `studies/data/spread` |
| `workflow-usdjpy-m30-2026-09-27` (+pdf) | the 25 steps run end to end on USDJPY M30 with the new `donchianUpperCrossUp` template, every test, and the incidents found (OPEN.md §57-§63) | report of the owner's 2026-09-26 night request; the template's reading awaits his confirmation |
| `manualIA-2026-09-28` (+pdf) | the night walk of the window as a person: every button from a chat prompt to a project, then every Python panel of Databanks and Estrategia on USDJPY M30; the ten fixes, and where it stopped (the custodian's 24 h guard, OPEN §83) | report of the owner's 2026-09-28 night request; the SQX half awaits his decision on the guard |
| `Ajedrez4D-2026-09-30` (+pdf) | the owner's explainer of the funded path, level by level: the floating from M1 (checked against SQX's MAE), one account as a state machine and the risk per trade, the three Monte Carlo (T1, T2, D) and the block length, the bank buying accounts on one long path, the choice with the haircut `h` and the monkey; 11 figures, two on real USDJPY data and nine from a toy simulator | explainer of `portfolio/PLAN.md` §14 — every toy number is illustrative |
| `catalogo-para-la-ui-2026-09-25` (+pdf) | outbound brief: everything the toolchain does, for whoever designs the window | inventory — goes stale |
| `paneles-flask-inventario-2026-09-25` | outbound brief: the depth of the three retired Flask panels, with the ten-point contract the «Estrategias» zone keeps | the bar for that zone |
| `respuestas-calidad-del-feed-2026-09-26` (pdf) | the owner's answers to the 16 decisions, with formulas | source of `ledger/thresholds.yaml` `feedQuality.` |
| `calidad-del-feed-decisiones-2026-09-26` (+pdf) | the 16 decisions the feed-quality module needs, each with a proposal measured on the M1 feed itself — replaces the outbound consultation | answered 2026-09-26 — the owner's answers and what the built module measured are its last section; the thresholds live in `ledger/thresholds.yaml` |
| `ideas-de-edge-2026-09-26` (+pdf) | the owner's dossier: what the project lacks to reach a quant desk's level — six ideas he accepted (full pass, positive controls, hypothesis space, ledger yield table, second data provider, cross-study multiplicity) and eight more | **accepted, no encargo yet** — an idea that becomes work moves to `docs/encargos/` |
| `ideas-de-internet-y-libros-2026-09-27` (+pdf) | the owner's dossier: 390 ideas from a web sweep and 24 of his algorithmic-trading books (eight reading agents), merged and explained in Spanish — what contradicts the project, a top 30, validation, hypotheses and data, costs/risk/live, process and UI | **catalogue, nothing accepted** — the 7 UI-only items were commissioned to the UI session (`scratch/ui-order-2026-09-27.md`) |

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
