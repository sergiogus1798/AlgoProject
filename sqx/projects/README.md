# sqx/projects — a project configured from assets/, not from its donor

| file | what it does | run it | in → out |
|---|---|---|---|
| `builder.py` | Turn a template plus an asset into a Builder project installed and ready to run — one command for what were five hand-edits of the task XML | `python3 -m sqx.projects.builder <name> --template <sqx> --symbol <SYM> [--role custodian] [--json]` | a template + `assets/<SYM>` → an installed `project.cfx`, verified |
| `setups.py` | One segment's window and costs into a task's `<Setup>` blocks — where a per-task cost actually lives | imported | an asset + a task XML → dates, slippage, spread, commission method and swap |
| `ranges.py` | The MC Retest spread and slippage ranges a task randomises within, from `assets/` | imported | an asset + a task XML → the task with its declared ranges |
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

**One segment per task.** With no `--segment`, each task takes its own from its type: `Build` →
`build`, everything else → `oos1`, per `assets/_policy.yaml`. That is the whole reason a `no_forex`
asset declares `spread_is` and `spread_oos` apart; forcing one segment on a chain prices the
retests with the build's spread and undoes it.

It refuses on three things: `oos2` (reserved for the WFC and the WFM — looking at it spends it), a
cost still carrying `use: null`, and a `.cfx` held by a running install, which rewrites it on exit.
It warns, without stopping, about PROVISIONAL figures and undecided MC Retest ranges.
