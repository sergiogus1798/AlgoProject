# AlgoProject

StrategyQuant X generates and robustness-tests strategies for MetaTrader 5; Python does the maths on
top. **Files in English. Talk to the owner in Spanish.**

## HARD RULES — ignoring one of these destroys work

1. **Every SQX sync deletes on-disk `.sqx` not held in memory.** Snapshot `user/projects` before
   anything that restarts SQX. → `knowhow/02-databanks.md`
2. **Never run `sqcli` on the master while its GUI is up** — use the worker on 5060. Never
   `pkill -f StrategyQuantX`: the pattern matches your own shell. Kill by PID.
3. **Never start a build, and never change what a project builds.** The master GUI and its projects
   are the owner's. Generic versus template generation is his decision, not a bug to fix — touch a
   project's config only when he names the project. Worker: one job, then `bin/sqx-worker.sh stop`.
4. **Never edit a `project.cfx` a running instance holds** — SQX rewrites the file on save and exit,
   and the change is silently lost. Use the `-project` API on the worker.
5. **Before authoring or modifying any project, task or template:** run
   `python3 -m core.assets <SYMBOL>`, report the overrides applied, and stop if it exits non-zero.
6. **Project names: underscores only.** The HTTP API splits its command on whitespace.
7. **Heavy data goes to the data root** (`~/Desktop/AlgoData`). Never write data into the repo.
8. **Writing Python? Read `CODESTYLE.md` first.** No absolute path outside `core/paths.py`. When
   done: `python3 tools/depmap.py && python3 tools/checks.py`.

## ROUTER — read only what the task needs

| task | read |
|---|---|
| a fact about formats, the API, exports, conditions | `knowhow/INDEX.md`, then that one file |
| writing or changing Python | `CODESTYLE.md`, then the folder's own `README.md` |
| authoring blocks, groups, templates, projects | `1_sqx/CLAUDE.md` |
| mass export and population maths | `2_tasks/CLAUDE.md` |
| one strategy in depth, or translating it to Python | `3_strategies/CLAUDE.md` |
| portfolios | `4_portfolio/CLAUDE.md` |
| what one SQX project actually does | `docs/<PROJECT>-pipeline.md`, TL;DR section only |
| what is broken or pending | `OPEN.md` |
| what data already exists | `~/Desktop/AlgoData/INDEX.md` |
| what the code imports | `docs/DEPENDENCIES.md` |

## Standing rule

Found a non-obvious fact? Write it into the right `knowhow/` file **in the same task**, tagged
🔬 tested · 📓 from logs · 🤔 inferred. A finding left in a transcript dies with the session. If it
contradicts this file, fix this file too.

## Layout

`core/` shared library · `1_sqx/` SQX surface · `2_tasks/` population analysis ·
`3_strategies/` single-strategy analysis · `4_portfolio/` portfolios · `5_mt5/` reserved ·
`assets/` cost overrides · `knowhow/` facts · `audit/` daily reports · `archive/` finished work,
unmaintained.

master `~/Desktop/SQX` · worker `~/Desktop/SQX_w1` (5060) · data `~/Desktop/AlgoData` ·
archive `~/Desktop/AlgoProject_Old` (read-only). Machine-specific paths: `config/machine.yaml`.
