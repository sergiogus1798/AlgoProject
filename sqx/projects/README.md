# sqx/projects — a project configured from assets/, not from its donor

| file | what it does | run it | in → out |
|---|---|---|---|
| `acceptance.py` | Write a cross-check's acceptance element: the conditions it judges by, and their thresholds. | importado | el catálogo + un crosscheck → su `<AcceptanceSettings>` reescrito |
| `buildcensus.py` | Count what a project's Build task will generate from: its shape, its blocks, its search and its acceptance. | `python3 -m sqx.projects.buildingblocks --project P --count` · `python3 -c "from pathlib import Path; from sqx.projects import buildcensus as b; print(b.census(Path('<cfx>')))"` | a `project.cfx` → a dict, or the lines a person reads |
| `builder.py` | Turn a template plus an asset into a Builder project installed and ready to run. | `python3 -m sqx.projects.builder Test_<name>\|Trade_<name> --purpose "..." (--template <sqx> \| --simple long\|short) [--random] --symbol <SYM> --timeframe <TF> [--workflow] [--acceptance calibration] [--minutes N --max-strategies N] [--role custodian] [--json]` | a template or a side + `assets/<SYM>` → an installed `project.cfx`, verified, and a row in the registry |
| `buildingblocks.py` | Write a palette into a project's Build task: which blocks the builder may draw for the free holes, and at what weight. | `python3 -m sqx.projects.buildingblocks --project P [--palette NAME[,NAME]] [--count] [--json] [--role custodian]` | a palette + a project → which blocks the builder may draw, counted |
| `buildrules.py` | The shape of the strategy a task may generate: how complex, which orders, which exits. | imported | a Build task → the same task with the generator bounded |
| `cfxio.py` | The one door for rewriting a project.cfx: refuse while an install holds it, replace atomically. | library, no `__main__` | `{member: bytes}` → the `.cfx`, or a refusal while an install is up |
| `charts.py` | The extra chart a multi-timeframe template needs, in the three places SQX reads it. | imported | a task XML + the project's extra streams → the same task able to test its strategies |
| `configure.py` | Write an asset's declared costs and one segment's window into every task of a project.cfx. | `python3 -m sqx.projects.configure <cfx> <SYMBOL> [--segment build\|oos1]` | a cloned `.cfx` + `assets/<SYMBOL>` → the same `.cfx`, priced and dated as declared |
| `crosschecks.py` | The surgery every cross-check configurator repeats: find the task, switch it on, silence it. | importado | una tarea → la misma tarea, con un solo crosscheck vivo |
| `crossfeeds.py` | Give a cross-check task the feed definitions of its extra markets, from SQX's registry. | imported | task XML + markets → task XML |
| `crossmarket.py` | Write the additional-markets cross-check from assets/: which markets, when, at what cost. | `python3 -m sqx.projects.crossmarket <SYM> [--cfx <cfx> --task <file> --timeframe <TF>]` | `_markets.yaml` + the markets' own files → the task's `<Setups>` |
| `crosstf.py` | Write the cross-timeframe check: the same asset and costs, one retest per timeframe. | `python3 -m sqx.projects.crosstf <SYM> --cfx <cfx> [--day YYYY-MM-DD]` | a project → its Cross TF tasks, plus `blocks.json` |
| `crosstfload.py` | Fill the two databanks Cross TF reads on disk, install stopped: its input (10.5) and the mothers MC Retest reads (13). | `python3 -m sqx.projects.crosstfload --project P --role custodian [--mothers]` | Cross Market output → `CrossTF_Input`; `CrossTF` → `CrossTF_Mothers` |
| `crosstfsolo.py` | Cross TF's extra timeframes, each a retest of its own copied from `CrossTF`. | imported by `crosstf.wire` | the configured `CrossTF` task → one task per extra timeframe |
| `databanks.py` | Which databank each task of a project reads and which it writes. | importado | proyecto → una fila por tarea |
| `doctrine.py` | Apply the owner's build doctrine to every task of a project, identically. | imported | a task + an asset + a timeframe → the task, generating and trading as declared |
| `exiting.py` | Stop a GUI session with a task still running: ask it to exit, let every other project save, then kill by PID. | imported | role + running project → one line saying how it went down |
| `forget.py` | Erase one named project everywhere: its live SQX project and every AlgoData folder it filled. | `python3 -m sqx.projects.forget <P>` · `... --yes` | a project name → every trace of it gone except its archived `.cfx` |
| `live.py` | Drive one headless GUI-mode SQX session (`bin/sqx-worker.sh --gui`) through the window's own /project servlet. | imported | a project on a live session → tasks run, databanks cut, disk == memory |
| `liveapi.py` | One POST to a GUI session's `/project` servlet, with the port and token SQX wrote to settings.xml. | imported (`live.call`, `live._setting`) | role, action, params → SQX's JSON reply |
| `loadwait.py` | The signals that SQX has finished something, from its own log: «Strategies loaded» after a `-databank action=load`, «APP LOADED» after a start. | imported | role, `live.mark` taken before the load, bound → returns or SystemExit |
| `mcretest.py` | Write the eight MC Retest tasks of a custom project: one perturbation each, as evidence. | `python3 -m sqx.projects.mcretest <SYM> --cfx <cfx> --input <databank>` | un `.cfx` + el catálogo de `_build.yaml` → las ocho tareas escritas, o desactivadas con el motivo |
| `mt5verify.py` | Write the MT5 bridge's check into a custom project: one retest per prop firm, and the EA's export. | imported by `mt5.verify.run` | a cloned `.cfx` + firms' costs → the same `.cfx` |
| `orders.py` | Whether a population trades with pending orders — what the builder allowed, what it emitted. | importado | la tarea Build y el databank → `stop/limit: sí, no, o sin resolver` |
| `patch.py` | Generic task-XML edits a build applies regardless of asset: template, caps, sync. | imported | a task XML → the same task, shaped, capped, syncing |
| `perturbations.py` | One MC Retest task: the perturbation it runs, the window it re-runs, its acceptance off. | importado | una tarea → la misma tarea, perturbando una sola cosa |
| `presaving.py` | Encargo 66 §7.1/7.4b: wait in the background for every project's databanks to load; save them at once (always on, owner 2026-10-13: the exit goes 52 s -> 15 s). | called by `live.py` | role → figures |
| `ranges.py` | The MC Retest perturbation ranges a task randomises within, taken from assets/. | imported | an asset + a task XML → the task with its declared ranges |
| `rankings.py` | Write the Build task's acceptance filters — its «Ranking» conditions — from assets/_study.yaml. | `python3 -m sqx.projects.rankings <cfx> <SYM> --timeframe <TF> [--acceptance study\|calibration] [--study-file <yaml>]` (project stopped) | a project.cfx + an asset + a timeframe → its Build task accepting by `_study.yaml` |
| `registry.py` | Who created each custom SQX project, for what, and whether it has been retired. | imported | a build's result → a row of `AlgoData/projects/registry.csv` |
| `registryxml.py` | A task's resources as SQX's data registry defines them today, in the exact text SQX writes. | imported | a task XML → the same task, resources as the registry has them |
| `resources.py` | Swap a clone's inherited feed for the asset it is meant to trade, borrowing the definition. | imported | a donor's tasks + a project that defines the feed, or the registry → every task on this asset's chart |
| `retire.py` | List the custom projects of every install, and retire the ones a finished run left behind. | `python3 -m sqx.projects.retire --list` · `python3 -m sqx.projects.retire <P>... --role custodian [--keep WFM] [--yes] [--own]` (`--own`: the caller built it in this same job — skips the 60-min freshness wait) | a project folder → `AlgoData/projects/retired/<install>/<P>-<date>.tar.gz`, registry stamped |
| `sessiondb.py` | Build a task's <Session> block from SQX's Data Manager database, read through a copy. | imported | a session name → its `<Session>` block, or None |
| `setups.py` | Write one segment's window and costs into a task's <Setup> blocks, which is where they live. | imported | an asset + a task XML → dates, slippage, spread, commission method, swap and data range |
| `source.py` | Find a project SQX itself wrote that defines an asset's feed, and its session when one does. | imported | donor + asset session and feed → a project.cfx, or None |
| `sources.py` | Every project the window can open, merged from the four places that each know part of it. | imported | disk → cards |
| `spp.py` | Write the two SPP tasks of a custom project: the permutation grid, one window each. | `python3 -m sqx.projects.spp <SYM> --cfx <cfx> --input <databank>` | un `.cfx` + el catálogo `spp:` de `_build.yaml` → `SPP IS` y `SPP OOS` escritas y activas |
| `stage.py` | Switch on only one workflow step's tasks, so `action=start` runs that step and nothing else. | `python3 -m sqx.projects.stage --cfx <cfx> --step build,oos` | a workflow project → the same project, one step switched on |
| `summary.py` | Say out loud what building a project applied, which is the half a human reads. | imported | `builder.build`'s result → the lines a human reads |
| `sweep.py` | Which custom projects the weekly cleanup retires: the owner's rule, as code. | `python3 -m ui.daemon.projects.janitor [--yes]` | the three installs → one keep/retire line per project, with its reason |
| `taskcap.py` | A live task's deadline: 3× the longest its title ever took in SQX's own log; past it, the abort. | imported | log lines → the abort of a task that does not advance |
| `tasksettings.py` | Task settings that must be identical across a whole project: timeframe, engine, MM, hours. | imported | a task → the same task, aligned with its siblings |
| `wfc.py` | Write the WFC/CSCV retest: one task per segment, each at its own costs, markets included. | `python3 -m sqx.projects.wfc <SYM> --cfx <cfx> --timeframe <TF> --tasks t1,t2,t3` | `wfc:` + `_markets.yaml` → three tasks writing three databanks |
| `wfm.py` | Write the Walk Forward Matrix task of a custom project: the grid, and the reserved window. | `python3 -m sqx.projects.wfm <SYM> --cfx <cfx> --input <databank>` | un `.cfx` + el catálogo `wfm:` → la tarea `WFM` escrita sobre `build..oos2`, con su criterio por casilla |
| `workflow.py` | Give a donor clone every task of the workflow: keep the steps' own, add the ones it lacks. | imported by `builder --workflow` | a donor clone → the whole workflow in one project |
| `buildmode_model.xml` | The owner's genetic settings, verbatim from the Build he configured by hand on 2026-10-02 (population 250 per island, 25 generations, 20 islands, no initial-population filter) | data | — |
| `stages.yaml` | Which task titles each workflow step runs | data | — |

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
on the master itself when nothing else defines the asset's feed, and on none at all when no project
does — the feed is then written from the master's data registry, through a copy; `resources.definitions`
takes exactly `<Symbol>`, `<InstrumentInfo>` and `<Broker>`, and `doctrine.borrow_session`
exactly one `<Session>` — from that project when it defines it, else built from the master's Data
Manager database (`sessiondb`, read through a copy; `tests/test_session_from_db.py`), else refused — never a `<Setup>`, a `<Task>`, a `<Databank>` or an acceptance/exit block.
The borrowed `<InstrumentInfo>` DOES embed the master's own cost blob (`defaultSpread`,
`commissions`, `swap` — its identity fields, the same ones a live install would rewrite on save,
hard rule 4), so the guarantee that matters is not "the text never appears" but "the text never
governs a backtest": `setups.py` always overwrites every `<Setup>` from `assets/`'s own declared
costs, per task, so the master's embedded figures stay inert. `tests/test_builder_scope.py` proves
both halves: `definitions()`/`borrow_session()` return only resource-shaped blocks, and a finished
project's `<Setup>`s carry `assets/`'s declared spread, never the master's (USDJPY: master 0.1,
`assets/symbols/USDJPY.yaml` 0.65 — the two never coincide by accident).

**What the Build accepts is data too, and it is no longer the donor's.** Until 2026-10-02 every
project inherited the frozen donor's `NumberOfTrades > 500 & SortinoRatio > 0.6 & Stagnation < 540`
(sampleType 127), which no file stated. `rankings.apply` now writes `assets/_study.yaml` into
`<Rankings><Conditions>` of the Build — scoped to `<Rankings>`, because the first `<Conditions>` of a
Build task is the initial population's under `<BuildMode>` — and the builder refuses a project whose
asset or timeframe has no value there. `--acceptance calibration` writes the relaxed set instead.
`tests/test_build_acceptance.py` holds the golden XML and the refusals; the card is
`knowhow/conditions/build-rankings-acceptance.md`.

**The doctrine is data, not code.** `assets/_build.yaml` holds what shape a strategy may have —
at most two entry and two exit conditions (counted per strategy in a Simple Strategy and per random
hole in a template — `buildrules.what_to_build`, `knowhow/authoring/condition-count-simple-vs-template.md`),
a lookback of one bar, market orders only, exits by bars
or by condition and never a stop or a target, ATR-based sizing, out on Friday at 21:00. It is
written into **every** task, because an IS and an OOS that differ in any of it are not comparable,
and comparing them is the only reason the OOS exists. The genetic settings are not parameterised at
all: the whole `<BuildMode>` block is a verbatim copy of the owner's own model project — only its
`generationType` is kept from the task, so a `--random` twin stays one
(`tests/test_builder_simple.py` compares a new project's block with the model and with his values).

**No template is a shape too.** `--simple long|short` builds a Simple Strategy: `StrategyType
simple`, `<MarketSides>` on that one side (the only direction gate there is without a template),
«What to build» entry 1..2 and exit 1..2. It still needs its palette — a project nobody applied one
to keeps the donor's 400 conditions — so count the Build before running it:
`python3 -m sqx.projects.buildingblocks --project P --palette <family> --count`.
→ `knowhow/authoring/simple-strategy-build-xml.md`

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
