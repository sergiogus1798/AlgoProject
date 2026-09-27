# sqx/projects — a project configured from assets/, not from its donor

| file | what it does | run it | in → out |
|---|---|---|---|
| `builder.py` | Turn a template plus an asset into a Builder project installed and ready to run — one command for what were five hand-edits of the task XML | `python3 -m sqx.projects.builder Test_<name>\|Trade_<name> --purpose "..." --template <sqx> --symbol <SYM> [--role custodian] [--json]` | a template + `assets/<SYM>` → an installed `project.cfx`, verified, and a row in the registry |
| `registry.py` | The name rule (`Test_` a functional test, `Trade_` real work) and the CSV of every project the builder created — who, when, what for, and when it was retired | imported | a build's result → a row of `AlgoData/projects/registry.csv` |
| `sweep.py` | The owner's weekly rule: retire `Test_`, anything under 10 tasks and the queue in `AlgoData/projects/retire-queue.txt`; keep `Trade_`, anything touched in 24 h, and every project of a running install | `python3 -m sqx.projects.retire --sweep [--yes]` | the three installs → one keep/retire line per project, with its reason |
| `retire.py` | List every custom project of the three installs, and retire the ones a finished run left behind: archive its `project.cfx` (and any databank named) and remove the folder | `python3 -m sqx.projects.retire --list` · `python3 -m sqx.projects.retire <P>... --role custodian [--keep WFM] [--yes]` | a project folder → `AlgoData/projects/retired/<install>/<P>-<date>.tar.gz`, registry stamped |
| `setups.py` | One segment's window and costs into a task's `<Setup>` blocks — where a per-task cost actually lives — and the matching data range in `<Resources><Symbol>`, which is which bars the task loads | imported | an asset + a task XML → dates, slippage, spread, commission method, swap and data range |
| `resources.py` | Swap a clone's inherited feed for the asset it must trade, borrowing the `<Symbol>`, `<InstrumentInfo>` and `<Broker>` from a project that already holds it — without it, a clone of the XAUUSD donor keeps trading gold and `setups.py` prices nothing | imported | a donor's tasks + a project that defines the feed → every task on this asset's chart |
| `source.py` | Pick the project a clone borrows its session and feed from when the donor lacks them: the newest `project.cfx` on any install defining both — so `builder` no longer needs `--session-from` for USDJPY | imported | donor + asset session and feed → a project.cfx, or None |
| `summary.py` | Say out loud what one build applied — the doctrine, the segments, the feed swap — with the provisional costs and the silenced acceptance last, where they are read | imported | `builder.build`'s result → the lines a human reads |
| `ranges.py` | The MC Retest spread and slippage ranges a task randomises within, from `assets/` | imported | an asset + a task XML → the task with its declared ranges |
| `doctrine.py` | Apply `assets/_build.yaml` to every task, and make them all carry the session they name | imported | a task + an asset + a timeframe → the task, generating and trading as declared |
| `buildrules.py` | What a generator may emit: how many conditions, which order types, which exits, no SL/PT | imported | a Build task → the same task with the generator bounded |
| `tasksettings.py` | What every task of a project must share: timeframe, engine, session, sizing, hours, cross-checks | imported | a task → the same task, aligned with its siblings |
| `buildmode_model.xml` | The owner's genetic settings, copied verbatim from his `XAUUSD_Breakout_H1` | data | — |
| `crossmarket.py` | The additional-markets cross-check: which markets, over what window (`crossmarket.segment`), at whose cost — all from `assets/`, with every acceptance condition silenced so it stays evidence | `python3 -m sqx.projects.crossmarket <SYM> [--cfx <cfx> --task <file> --timeframe <TF>]` | `_markets.yaml` + the markets' own files → the task's `<Setups>` |
| `databanks.py` | qué databank lee y qué escribe cada tarea, y encadena el input de cada una con el output de la anterior | importado | proyecto → una fila por tarea |
| `crosstf.py` | The **same** asset read on other timeframes: one `<Setup>` per timeframe whose only override is the timeframe, with the cross-check's acceptance silenced so it stays evidence | `python3 -m sqx.projects.crosstf <SYM> --cfx <cfx> --task <file> [--timeframes H4]` | a task → its `<Setups>`, plus the block order `studies/transfer/crossTF/` must agree with |
| `wfc.py` | The WFC/CSCV retest: three tasks, one per segment, each at its own spread and slippage, each with the cross-market check inside and every acceptance condition silenced | `python3 -m sqx.projects.wfc <SYM> --cfx <cfx> --timeframe <TF> --tasks t1,t2,t3` | `wfc:` + `_markets.yaml` → three tasks writing three databanks |
| `mcretest.py` | Las ocho tareas MC Retest de un proyecto: cuál perturba qué, sobre qué ventana, leyendo todas el mismo databank | `python3 -m sqx.projects.mcretest <SYM> --cfx <cfx> --input <databank>` | un `.cfx` + el catálogo de `_build.yaml` → las ocho tareas escritas, o desactivadas con el motivo |
| `perturbations.py` | Una tarea MC Retest: el método que sortea, la ventana que vuelve a correr, su aceptación apagada | importado | una tarea → la misma tarea, perturbando una sola cosa |
| `orders.py` | Si la población opera con órdenes pendientes — lo que el generador permitió y lo que las estrategias llevan de verdad | importado | la tarea Build y el databank → `stop/limit: sí, no, o sin resolver` |
| `crosschecks.py` | La cirugía que repiten todos los configuradores de crosscheck: encontrar la tarea por su título, encenderla, callar su aceptación y dejar sólo los parámetros recomendados | importado | una tarea → la misma tarea, con un solo crosscheck vivo |
| `acceptance.py` | Cómo juzga un crosscheck: las condiciones que evalúa en cada celda y los umbrales del elemento `<Conditions>` — incluida el área que la WFM busca en su matriz | importado | el catálogo + un crosscheck → su `<AcceptanceSettings>` reescrito |
| `spp.py` | Las dos tareas SPP de un proyecto: la rejilla de permutación, una ventana cada una, sin que ninguna filtre | `python3 -m sqx.projects.spp <SYM> --cfx <cfx> --input <databank>` | un `.cfx` + el catálogo `spp:` de `_build.yaml` → `SPP IS` y `SPP OOS` escritas y activas |
| `wfm.py` | La tarea Walk Forward Matrix: los dos ejes de la rejilla, y la ventana que la política reserva | `python3 -m sqx.projects.wfm <SYM> --cfx <cfx> --input <databank>` | un `.cfx` + el catálogo `wfm:` → la tarea `WFM` escrita sobre `build..oos2`, con su criterio por casilla |
| `stage.py` | Leave only one workflow step's tasks active, so `action=start` runs that step and skips the rest; every configurator calls it for its own step | `python3 -m sqx.projects.stage --cfx <cfx> --step build,oos` | a workflow project → the same project, one step switched on |
| `stages.yaml` | Which task titles each workflow step runs | data | — |
| `workflow.py` | Give a donor clone every task of the workflow: keep the steps' own, add CrossTF and the three WFC legs, wire their databanks | imported by `builder --workflow` | a donor clone → the whole workflow in one project |
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
