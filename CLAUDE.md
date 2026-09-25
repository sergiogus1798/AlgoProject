# AlgoProject

StrategyQuant X generates and robustness-tests strategies for MetaTrader 5; Python does the maths on
top. **Talk to the owner in Spanish.** Code, `knowhow/` and the `README.md` of code folders are in
English; **`docs/manual/`, `docs/AgentPDFs/`, `docs/preregistro/` and `docs/encargos/` are in
Spanish, because their reader is the owner.** Do not "fix" them.

## HARD RULES — ignoring one of these destroys work

1. **Every SQX sync deletes on-disk `.sqx` not held in memory.** Snapshot `user/projects` before
   anything that restarts SQX. → `knowhow/databanks/sync-deletes-unloaded-files.md`
2. **Never run `sqcli` on the master while its GUI is up** — use the worker on 5060. Never
   `pkill -f StrategyQuantX`: the pattern matches your own shell. Kill by PID.
3. **The master is the owner's; the workers are yours.** Never start a build on the master and
   never change what one of its projects builds — generic versus template generation, an inactive
   task, what a task clears: his decisions, not bugs to fix and **not findings to report**. Touch a
   master project's config only when he names the project. **On the two headless workers you may
   author, configure and build freely** (owner, 2026-09-22): conductor `SQX_w1`/5060 for authoring
   and queries, custodian `SQX_w2`/5070 for the one long job at a time. Either way: one job, then
   `bin/sqx-worker.sh [--role ROLE] stop`.
4. **Never edit a `project.cfx` a running instance holds** — SQX rewrites the file on save and exit,
   and the change is silently lost. Use the `-project` API on the worker.
5. **Before authoring or modifying any project, task or template:** run
   `python3 -m core.assets <SYMBOL>`, report the overrides applied, and stop if it exits non-zero.
6. **Project names: underscores only.** The HTTP API splits its command on whitespace.
7. **Heavy data goes to the data root** (`~/Desktop/AlgoData`). Never write data into the repo.
8. **A new command ships with its manual page, in the same task.** Copy
   `docs/manual/_PLANTILLA.md` to `docs/manual/NN-<name>.md`, in Spanish, with screenshots of
   real output. `checks.py` fails on a `__main__` that no manual page names, neither by its path
   nor by its `python3 -m` dotted form.
   `docs/manual/PENDIENTE.md` is inherited backlog only — nothing new goes in it.
9. **Writing Python? Read `CODESTYLE.md` first.** No absolute path outside `core/paths.py`. When
   done: `python3 tools/depmap.py && python3 tools/checks.py`.

10. **Every SQX run happens in a CUSTOM PROJECT — never in the stock `Builder` or `Retester`.**
    Owner, 2026-09-23. A test on a template, a symbol or a timeframe gets a project of its own,
    cloned from the frozen donor by `sqx/projects/builder.py`, or an existing custom project reused
    by name. The stock projects are not harnesses: they carry someone else's costs, someone else's
    databanks and someone else's task chain, and a run inside one is unattributable afterwards.
    Per-task costs are what makes this work — one project holds the build on `build` and the
    retests on `oos1`, each with its own spread, slippage, swap, asset and cross-checks.

## ROUTER — read only what the task needs

| task | read |
|---|---|
| a fact about formats, the API, exports, conditions, costs, research, perf | `grep -rh '^q:' knowhow/<domain>/`, then read only the card's header (up to `## Evidence`) — domains in `knowhow/INDEX.md` |
| writing or changing Python | `CODESTYLE.md`, then the folder's own `README.md` |
| authoring blocks, groups, templates, projects | `sqx/CLAUDE.md` |
| mass export and population maths | `tasks/CLAUDE.md` |
| one strategy in depth, or translating it to Python | `strategies/CLAUDE.md` |
| portfolios | `portfolio/CLAUDE.md` |
| whether a result beats random entry, and which channel the edge lives in | `nulls/README.md` |
| cribar una poblacion OOS entera hasta una lista de supervivientes | `gate/README.md` |
| running something, or explaining to a human how to | `docs/manual/` — `00-empezar.md`, then that module's page |
| what one SQX project actually does | regenerate on demand: `sqx/inspect/dump_project.py <PROJECT>` (`OPEN.md`) |
| what is broken or pending | `OPEN.md` |
| **la secuencia entera, de la idea a la estrategia superviviente — los 20 pasos y en cuál estás** | `docs/AgentPDFs/WORKFLOW.md` — manda sobre el orden que digan los otros dos dossiers |
| **what to work on next, and who does it** — the whole remaining programme split into dispatchable tasks | `docs/AgentPDFs/plan-ejecucion-2026-09-21.md` |
| the XAUUSD robustness protocol: what is built, what is left, and the contracts between them | `docs/AgentPDFs/protocolo-robustez-2026-09-21.md` |
| **la ventana de escritorio: la librería de plantillas, su cobertura y el chat que redacta una nueva** | `ui/README.md`, then `docs/manual/35-app-plantillas.md` |
| **los activos: costes, tramos, rangos y doctrina, sin abrir un YAML** | `assets/RULES.md`, then `docs/manual/38-app-activos.md` — la ventana los escribe, `core.assetwrite` es el único escritor |
| what anything costs in time, memory or disk | `docs/manual/12-rendimiento.md`, then `perf/README.md` |
| what data already exists | `~/Desktop/AlgoData/INDEX.md` |
| **what skills exist, what each is for, and which are candidates to retire** | `docs/SKILLS.md` — generated by `tools/skillmap.py` |
| what the code imports | `docs/DEPENDENCIES.md` |

## Standing rule

Found a non-obvious fact? Write it as a card in `knowhow/<domain>/` **in the same task** — edit the
card that exists, never append; format in `knowhow/INDEX.md` — tagged 🔬 tested · 📓 from logs ·
🤔 inferred. A finding left in a transcript dies with the session. If it contradicts this file, fix
this file too.

## Layout

`ui/` the desktop app (window + local daemon) · `core/` shared library · `sqx/` SQX surface · `tasks/` population analysis ·
`strategies/` single-strategy analysis · `portfolio/` portfolios · `perf/` cost catalogue ·
`nulls/` entry-timing nulls · `ledger/` the global search ledger and the frozen thresholds ·
`mt5/` reserved ·
`assets/` cost overrides · `knowhow/` facts · `audit/` daily reports · `archive/` finished work,
unmaintained.

master `~/Desktop/SQX` · worker `~/Desktop/SQX_w1` (5060) · data `~/Desktop/AlgoData` ·
archive `~/Desktop/AlgoProject_Old` (read-only). Machine-specific paths: `config/machine.yaml`.
