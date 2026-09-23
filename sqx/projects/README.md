# sqx/projects — a project configured from assets/, not from its donor

| file | what it does | run it | in → out |
|---|---|---|---|
| `builder.py` | Turn a template plus an asset into a Builder project installed and ready to run — one command for what were five hand-edits of the task XML | `python3 -m sqx.projects.builder <name> --template <sqx> --symbol <SYM> [--role custodian] [--json]` | a template + `assets/<SYM>` → an installed `project.cfx`, verified |
| `ranges.py` | The MC Retest spread and slippage ranges a task randomises within, from `assets/` | imported | an asset + a task XML → the task with its declared ranges |
| `configure.py` | Write an asset's declared costs and each task's own segment window into a `project.cfx` | `python3 -m sqx.projects.configure <cfx> <SYMBOL> [--segment build\|oos1]` | a cloned `.cfx` + `assets/<SYMBOL>` → the same `.cfx`, priced and dated as declared |

**Why this exists.** A project is cloned from a donor, and the donor carries the **master's own
live settings**, which are not the declared policy. On XAUUSD the donor charges `SizeBased 8` where
`assets/` says `PercentageBased 0.00174`, and no slippage where `assets/` says five points. Nothing
errors if the clone is used as-is: the build simply runs at a cost nobody chose.

**One segment per task, not per project.** SQX stores costs per symbol **inside each task**, so the
Build task carries one `defaultSpread` and the retest tasks another — which is the whole reason a
`no_forex` asset declares `spread_is` and `spread_oos` apart. With no `--segment`, each task takes
its own from its type: `Build` → `build`, everything else → `oos1`, per `assets/_policy.yaml`.
Forcing one segment on a whole chain prices the retests with the build's spread and undoes it.

It refuses on three things: `oos2` (reserved for the WFC and the WFM — looking at it spends it), a
cost still carrying `use: null`, and a `.cfx` held by a running install, which rewrites it on exit.
It warns, without stopping, about PROVISIONAL figures and undecided MC Retest ranges.
