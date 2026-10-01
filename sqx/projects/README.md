# sqx/projects — a project configured from assets/, not from its donor

| file | what it does | run it | in → out |
|---|---|---|---|
| `builder.py` | Turn a template plus an asset into a Builder project installed and ready to run — one command for what were five hand-edits of the task XML | `python3 -m sqx.projects.builder Test_<name>\|Trade_<name> --purpose "..." --template <sqx> --symbol <SYM> [--role custodian] [--json]` | a template + `assets/<SYM>` → an installed `project.cfx`, verified, and a row in the registry |
| `registry.py` | The name rule (`Test_` a functional test, `Trade_` real work) and the CSV of every project the builder created — who, when, what for, and when it was retired | imported | a build's result → a row of `AlgoData/projects/registry.csv` |
| `sweep.py` | The owner's weekly rule: retire `Test_`, anything under 10 tasks and the queue in `AlgoData/projects/retire-queue.txt`; keep `Trade_`, anything touched in 24 h, and every project of a running install | `python3 -m sqx.projects.retire --sweep [--yes]` | the three installs → one keep/retire line per project, with its reason |
| `retire.py` | List every custom project of the three installs, and retire the ones a finished run left behind: archive its `project.cfx` (and any databank named) and remove the folder | `python3 -m sqx.projects.retire --list` · `python3 -m sqx.projects.retire <P>... --role custodian [--keep WFM] [--yes] [--own]` (`--own`: the caller built it in this same job — skips the 60-min freshness wait) | a project folder → `AlgoData/projects/retired/<install>/<P>-<date>.tar.gz`, registry stamped |
| `forget.py` | Erase a named project everywhere, not just retire it: the live project on conductor/custodian (via `retire.py`, so its `.cfx` is still archived) plus every `AlgoData` folder that nests a subfolder of its name (`raw/`, `harvest/`, `metrics/`, `reports/`, `structural/`, `strategyPermutations/`, `atrCalculator/`, `crosstf/`) — the parquet and CSVs `retire.py` deliberately leaves behind. Refuses a stock project and anything that lives only on the master (hard rule 3) | `python3 -m sqx.projects.forget <P>` · `... --yes` | a project name → every trace of it gone except its archived `.cfx` |
| `setups.py` | One segment's window and costs into a task's `<Setup>` blocks (`write_setup` takes costs priced elsewhere — a prop firm's, for `mt5verify`) — where a per-task cost actually lives — and the matching data range in `<Resources><Symbol>`, which is which bars the task loads | imported | an asset + a task XML → dates, slippage, spread, commission method, swap and data range |
| `resources.py` | Swap a clone's inherited feed for the asset it must trade, borrowing the `<Symbol>`, `<InstrumentInfo>` and `<Broker>` from a project that already holds it — without it, a clone of the XAUUSD donor keeps trading gold and `setups.py` prices nothing. `refuse()` is the last gate `builder.build` runs before a staged project is moved into an install: a template that would be ignored, a task with zero priced Setups, or the donor's own feed still readable anywhere after the swap | imported | a donor's tasks + a project that defines the feed → every task on this asset's chart |
| `registryxml.py` | A task's resources rebuilt from SQX's data registry (`data.db`) in the exact text SQX writes — `refresh()` brings every `<Symbol>` to its feed's timezone, data broker and instrument and rebuilds `<Instruments>`; SQX compares instruments as text and refuses to start a task that differs («unresolved resources»). The builder runs it on every task (2026-10-01, feeds moved to EETUS) | imported | a task XML → the same task, resources as the registry has them |
| `live.py` | One headless GUI-mode session (`bin/sqx-worker.sh --gui`) driven through the window's own `/project` servlet with the `browserToken` SQX writes to settings.xml: `mine`, `start`/`stop`, `push` (a configured copy's task XMLs → `updateTaskXML`), `run` (start with `projectXML`, wait for the end in SQX's log so no agent reads it), `sync` (memory → disk), `cut` (`removeReports` + sync). `knowhow/sqx-drive/live-chain-without-restart.md` | imported | a project on a live session → tasks run, databanks cut, disk == memory |
| `patch.py` | The task-XML edits every build applies regardless of asset: point a Build task at its template, cap strategies and minutes, and switch a databank from "Auto-sync never" to syncing | imported | a task XML → the same task, templated, capped, syncing |
| `source.py` | Pick the project a clone borrows its session and feed from when the donor lacks them: the newest `project.cfx` on any install defining both — so `builder` no longer needs `--session-from` for USDJPY | imported | donor + asset session and feed → a project.cfx, or None |
| `summary.py` | Say out loud what one build applied — the doctrine, the segments, the feed swap — with the provisional costs and the silenced acceptance last, where they are read | imported | `builder.build`'s result → the lines a human reads |
| `ranges.py` | The MC Retest spread and slippage ranges a task randomises within, from `assets/` | imported | an asset + a task XML → the task with its declared ranges |
| `doctrine.py` | Apply `assets/_build.yaml` to every task, and make them all carry the session they name | imported | a task + an asset + a timeframe → the task, generating and trading as declared |
| `buildrules.py` | What a generator may emit: how many conditions, which order types, which exits, no SL/PT | imported | a Build task → the same task with the generator bounded |
| `tasksettings.py` | What every task of a project must share: timeframe, engine, session, sizing, hours, cross-checks | imported | a task → the same task, aligned with its siblings |
| `buildmode_model.xml` | The owner's genetic settings, copied verbatim from his `XAUUSD_Breakout_H1` | data | — |
| `crossmarket.py` | The additional-markets cross-check: which markets, over what window (`crossmarket.segment`), at whose cost — all from `assets/`, with every acceptance condition silenced so it stays evidence | `python3 -m sqx.projects.crossmarket <SYM> [--cfx <cfx> --task <file> --timeframe <TF>]` | `_markets.yaml` + the markets' own files → the task's `<Setups>` |
| `databanks.py` | qué databank lee y qué escribe cada tarea, y encadena el input de cada una con el output de la anterior | importado | proyecto → una fila por tarea |
| `crosstf.py` | The **same** asset read on other timeframes, one retest per timeframe (owner, 2026-09-30 — never blocks of `RetestOnAdditionalMarkets`, whose `data=all` export cannot be split on one symbol): `CrossTF` on the source timeframe over `crosstf.segment` at `crosstf.precision`, its cross-check off and its acceptance silenced, then one «CrossTF <TF>» per `crosstf.timeframes` entry (`crosstfsolo`); files `blocks.json` (`blocks` and `databanks`, in order) under `core.datapaths.crosstf_dir(project, --day)` so the study never re-reads this run off a doctrine that may since have changed (OPEN.md #80) | `python3 -m sqx.projects.crosstf <SYM> --cfx <cfx> [--day YYYY-MM-DD]` | a project → its Cross TF tasks, plus `blocks.json` |
| `buildingblocks.py` | Step 6: a palette (`sqx/blocks/palettes/`) written into every Build task's `<BuildingBlocks>` — `use` and `weight` per block from `palette.resolve`, the role prefix (`Indicators.`, `Stop/Limit Price Levels.`) stripped to the taxonomy's key, a key outside the taxonomy switched off; refuses while the install is up (hard rule 4). The `buildingBlocksExpert` agent chooses the palette | `python3 -m sqx.projects.buildingblocks --project P --palette NAME [--role custodian]` | a palette + a project → which blocks the free holes may draw |
| `crosstfload.py` | Fills, on disk and with the install stopped, the two databanks no task writes: `CrossTF_Input` (step 10.5 — the Cross Market survivors scaled by `sqx.variants.scale` to `crosstf.timeframes`, plus the mothers, with the `CrossTF` task rewired to those blocks) and `CrossTF_Mothers` (before 13 — what `CrossTF` holds minus the `_Scaled*` siblings; the MC Retest reads it). The window's launchers call it (`ui/daemon/launch/run.py`, `ui/daemon/advance/run.py`) | `python3 -m sqx.projects.crosstfload --project P --role custodian [--mothers]` | Cross Market output → `CrossTF_Input`; `CrossTF` → `CrossTF_Mothers` |
| `crosstfsolo.py` | One Cross TF timeframe as a task of its own («CrossTF M30» → `CrossTF_M30`, …), copied from the configured `CrossTF` task — same window, costs and precision — on its timeframe and on `crosstf.engines`' engine for it, else the doctrine's: D1 on MetaTrader 4 (owner, 2026-09-30: on MT5 a D1 strategy enters at 00:00 and a prop firm's session opens at 00:05, so it traded nothing) | imported by `crosstf.wire` | the configured `CrossTF` task → one task per extra timeframe |
| `wfc.py` | The WFC/CSCV retest: three tasks, one per segment, each at its own spread and slippage, each with the cross-market check inside and every acceptance condition silenced | `python3 -m sqx.projects.wfc <SYM> --cfx <cfx> --timeframe <TF> --tasks t1,t2,t3` | `wfc:` + `_markets.yaml` → three tasks writing three databanks |
| `mcretest.py` | Las ocho tareas MC Retest de un proyecto: cuál perturba qué, sobre qué ventana, leyendo todas el mismo databank | `python3 -m sqx.projects.mcretest <SYM> --cfx <cfx> --input <databank>` | un `.cfx` + el catálogo de `_build.yaml` → las ocho tareas escritas, o desactivadas con el motivo |
| `perturbations.py` | Una tarea MC Retest: el método que sortea, la ventana que vuelve a correr, su aceptación apagada | importado | una tarea → la misma tarea, perturbando una sola cosa |
| `orders.py` | Si la población opera con órdenes pendientes — lo que el generador permitió y lo que las estrategias llevan de verdad | importado | la tarea Build y el databank → `stop/limit: sí, no, o sin resolver` |
| `crosschecks.py` | La cirugía que repiten todos los configuradores de crosscheck: encontrar la tarea por su título, encenderla, callar su aceptación y dejar sólo los parámetros recomendados | importado | una tarea → la misma tarea, con un solo crosscheck vivo |
| `acceptance.py` | Cómo juzga un crosscheck: las condiciones que evalúa en cada celda y los umbrales del elemento `<Conditions>` — incluida el área que la WFM busca en su matriz | importado | el catálogo + un crosscheck → su `<AcceptanceSettings>` reescrito |
| `spp.py` | Las dos tareas SPP de un proyecto: la rejilla de permutación, una ventana cada una, sin que ninguna filtre | `python3 -m sqx.projects.spp <SYM> --cfx <cfx> --input <databank>` | un `.cfx` + el catálogo `spp:` de `_build.yaml` → `SPP IS` y `SPP OOS` escritas y activas |
| `wfm.py` | La tarea Walk Forward Matrix: los dos ejes de la rejilla, y la ventana que la política reserva | `python3 -m sqx.projects.wfm <SYM> --cfx <cfx> --input <databank>` | un `.cfx` + el catálogo `wfm:` → la tarea `WFM` escrita sobre `build..oos2`, con su criterio por casilla |
| `stage.py` | Leave only one workflow step's tasks active, so `action=start` runs that step and skips the rest; every configurator calls it for its own step; `just(cfx, titles)` switches on tasks by title, for the window's «Lanzar en SQX» | `python3 -m sqx.projects.stage --cfx <cfx> --step build,oos` | a workflow project → the same project, one step switched on |
| `stages.yaml` | Which task titles each workflow step runs | data | — |
| `workflow.py` | Give a donor clone every task of the workflow: keep the steps' own, add CrossTF and the three WFC legs, wire their databanks | imported by `builder --workflow` | a donor clone → the whole workflow in one project |
| `mt5verify.py` | MT5 Bridge's check in a `Test_MT5Verify_…` project: two of the donor's retests become one per prop firm — its costs (`mt5.verify.conditions`) through `setups.write_setup`, the owner's window, no out-of-sample split, every cross-check off and every condition silenced — plus a SaveToFiles task exporting the EA as MQL5 (`Expert Advisor for MetaTrader5 (*.MQ5)`, magic from 1); only those three switched on | imported by `mt5.verify.run` | a cloned `.cfx` + firms' costs → the same `.cfx` |
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

**From the master, a new project may take ONLY bar data, instrument definitions and trading
sessions — never any task configuration** (owner, 2026-09-29). `source.pick` may land on a project
on the master itself when nothing else defines the asset's session or feed; `resources.definitions`
then borrows exactly `<Symbol>`, `<InstrumentInfo>` and `<Broker>`, and `doctrine.borrow_session`
exactly one `<Session>` — never a `<Setup>`, a `<Task>`, a `<Databank>` or an acceptance/exit block.
The borrowed `<InstrumentInfo>` DOES embed the master's own cost blob (`defaultSpread`,
`commissions`, `swap` — its identity fields, the same ones a live install would rewrite on save,
hard rule 4), so the guarantee that matters is not "the text never appears" but "the text never
governs a backtest": `setups.py` always overwrites every `<Setup>` from `assets/`'s own declared
costs, per task, so the master's embedded figures stay inert. `tests/test_builder_scope.py` proves
both halves: `definitions()`/`borrow_session()` return only resource-shaped blocks, and a finished
project's `<Setup>`s carry `assets/`'s declared spread, never the master's (USDJPY: master 0.1,
`assets/symbols/USDJPY.yaml` 0.65 — the two never coincide by accident).

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

⚠️ **`wfm.py` ends its window in `oos2`.** For a human every command may point at `oos2`
(owner, 2026-09-28); under `ALGO_AUTONOMOUS=1` only the WFM and the WFC may, and everything else
refuses it.

It refuses on three things: `oos2` (only for an autonomous agent, `ALGO_AUTONOMOUS=1`; a human may
ask for it since 2026-09-28), a
cost still carrying `use: null`, and a `.cfx` held by a running install, which rewrites it on exit.
It warns, without stopping, about PROVISIONAL figures and undecided MC Retest ranges.
