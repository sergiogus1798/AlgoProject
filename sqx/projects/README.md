# sqx/projects — a project configured from assets/, not from its donor

| file | what it does | run it | in → out |
|---|---|---|---|
| `builder.py` | Turn a template plus an asset into a Builder project installed and ready to run — one command for what were five hand-edits of the task XML | `python3 -m sqx.projects.builder <name> --template <sqx> --symbol <SYM> [--role custodian] [--json]` | a template + `assets/<SYM>` → an installed `project.cfx`, verified |
| `setups.py` | One segment's window and costs into a task's `<Setup>` blocks — where a per-task cost actually lives | imported | an asset + a task XML → dates, slippage, spread, commission method and swap |
| `ranges.py` | The MC Retest spread and slippage ranges a task randomises within, from `assets/` | imported | an asset + a task XML → the task with its declared ranges |
| `doctrine.py` | Apply `assets/_build.yaml` to every task, and make them all carry the session they name | imported | a task + an asset + a timeframe → the task, generating and trading as declared |
| `buildrules.py` | What a generator may emit: how many conditions, which order types, which exits, no SL/PT | imported | a Build task → the same task with the generator bounded |
| `tasksettings.py` | What every task of a project must share: timeframe, engine, session, sizing, hours, cross-checks | imported | a task → the same task, aligned with its siblings |
| `buildmode_model.xml` | The owner's genetic settings, copied verbatim from his `XAUUSD_Breakout_H1` | data | — |
| `crossmarket.py` | The additional-markets cross-check: which markets, over what window, at whose cost — all from `assets/` | `python3 -m sqx.projects.crossmarket <SYM> [--cfx <cfx> --task <file> --timeframe <TF>]` | `_markets.yaml` + the markets' own files → the task's `<Setups>` |
| `databanks.py` | qué databank lee y qué escribe cada tarea, y encadena el input de cada una con el output de la anterior | importado | proyecto → una fila por tarea |
| `crosstf.py` | The **same** asset read on other timeframes: one `<Setup>` per timeframe whose only override is the timeframe, with the cross-check's acceptance silenced so it stays evidence | `python3 -m sqx.projects.crosstf <SYM> --cfx <cfx> --task <file> --timeframes H4 D1` | a task → its `<Setups>`, plus the block order `strategies/crossTF/` must agree with |
| `mcretest.py` | Las ocho tareas MC Retest de un proyecto: cuál perturba qué, sobre qué ventana, leyendo todas el mismo databank | `python3 -m sqx.projects.mcretest <SYM> --cfx <cfx> --input <databank>` | un `.cfx` + el catálogo de `_build.yaml` → las ocho tareas escritas, o desactivadas con el motivo |
| `perturbations.py` | Una tarea MC Retest: el método que sortea, la ventana que vuelve a correr, su aceptación apagada | importado | una tarea → la misma tarea, perturbando una sola cosa |
| `orders.py` | Si la población opera con órdenes pendientes — lo que el generador permitió y lo que las estrategias llevan de verdad | importado | la tarea Build y el databank → `stop/limit: sí, no, o sin resolver` |
| `crosschecks.py` | La cirugía que repiten todos los configuradores de crosscheck: encontrar la tarea por su título, encenderla, callar su aceptación y dejar sólo los parámetros recomendados | importado | una tarea → la misma tarea, con un solo crosscheck vivo |
| `spp.py` | Las dos tareas SPP de un proyecto: la rejilla de permutación, una ventana cada una, sin que ninguna filtre | `python3 -m sqx.projects.spp <SYM> --cfx <cfx> --input <databank>` | un `.cfx` + el catálogo `spp:` de `_build.yaml` → `SPP IS` y `SPP OOS` escritas y activas |
| `wfm.py` | La tarea Walk Forward Matrix: los dos ejes de la rejilla, y la ventana que la política reserva | `python3 -m sqx.projects.wfm <SYM> --cfx <cfx> --input <databank>` | un `.cfx` + el catálogo `wfm:` → la tarea `WFM` escrita sobre `oos2` |
| `configure.py` | Write an asset's declared costs and each task's own segment window into a `project.cfx` | `python3 -m sqx.projects.configure <cfx> <SYMBOL> [--segment build\|oos1]` | a cloned `.cfx` + `assets/<SYMBOL>` → the same `.cfx`, priced and dated as declared |

**Why this exists.** A project is cloned from a donor, and the donor carries the **master's own
live settings**, which are not the declared policy. Nothing errors if the clone is used as-is: the
build simply runs at a cost nobody chose.

⚠️ **Costs go in `<Setup>`, never in `<Resources><Symbol><InstrumentInfo>`.** The first is the
per-task cost configuration — dates, slippage, the `<Chart>`'s spread, the commission method, the
swap — and it is what the GUI edits when a task is given its own. The second is the instrument
DEFINITION, which must agree with SQX's own registry; editing it is what produces
`Project has unresolved resources`, measured 2026-09-23. That is also why **one project really does
carry two segments**: the build task on `build`, the retests on `oos1`, each with its own costs.

**The doctrine is data, not code.** `assets/_build.yaml` holds what shape a strategy may have —
at most two entry and two exit conditions, a lookback of one bar, market orders only, exits by bars
or by condition and never a stop or a target, ATR-based sizing, out on Friday at 21:00. It is
written into **every** task, because an IS and an OOS that differ in any of it are not comparable,
and comparing them is the only reason the OOS exists. The genetic settings are not parameterised at
all: the whole `<BuildMode>` block is a verbatim copy of the owner's own model project.

⚠️ **A task can name a session it does not define, and trades the wrong hours in silence.** The
donor does exactly that — its Build defines `XAUUSD_the5ers` and its Retest `XAUUSD_ftmo` — so
`doctrine.unify_sessions()` copies the definition into every task that was missing it.

**One segment per task.** With no `--segment`, each task takes its own from its type: `Build` →
`build`, everything else → `oos1`, per `assets/_policy.yaml`. That is the whole reason a `no_forex`
asset declares `spread_is` and `spread_oos` apart; forcing one segment on a chain prices the
retests with the build's spread and undoes it.

⚠️ **`wfm.py` is the one command that writes `oos2`**, and it is the exception `configure.py`'s
refusal exists for: the walk-forward matrix is what that window is reserved *for*. Everything else
still refuses it, and the WFM's own output says so every time it runs.

It refuses on three things: `oos2` (reserved for the WFC and the WFM — looking at it spends it), a
cost still carrying `use: null`, and a `.cfx` held by a running install, which rewrites it on exit.
It warns, without stopping, about PROVISIONAL figures and undecided MC Retest ranges.
