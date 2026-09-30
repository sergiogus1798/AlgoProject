# AlgoProject

StrategyQuant X generates and robustness-tests strategies for MetaTrader 5; Python does the maths on top.
**Talk to the owner in Spanish.** The language follows the reader: **what the owner reads is in Spanish**
— `docs/manual/`, `docs/AgentPDFs/`, `docs/encargos/`, the window's text; **what code or an agent reads is
in English** — code, `knowhow/`, the `README.md` of code folders, the `CLAUDE.md` files. A new folder
follows the same test. Do not "fix" either side.

## HARD RULES — ignoring one of these destroys work

Rules 2, 4, 7 and 12 are also enforced by the PreToolUse guard `.claude/hooks/guard.py`: a block from
it is the rule firing, never something to route around. → `knowhow/eng/claude-hooks-guard.md`

1. **Every SQX sync deletes on-disk `.sqx` not held in memory.** Snapshot `user/projects` before anything
   that restarts SQX. → `knowhow/databanks/sync-deletes-unloaded-files.md`
2. **Never run `sqcli` on the master while its GUI is up** — use the conductor, `SQX_w1` on 5060. Never
   `pkill -f StrategyQuantX`: the pattern matches your own shell. Kill by PID.
3. **Three installs, three owners of the decision.** → `knowhow/sqx-drive/three-install-topology.md`

   | install | port | whose | for | heap |
   |---|---|---|---|---|
   | master `SQX` | 5050 | **the owner's** | his GUI; he rarely opens it now | 24g |
   | conductor `SQX_w1` | 5060 | yours (owner, 2026-09-22) | authoring, queries, exports; short jobs | 16g |
   | custodian `SQX_w2` | 5070 | yours | **one** long job at a time, all cores | 80g |

   - **Master:** never build there, and never change what a project builds — generic vs template
     generation, an inactive task, what a task clears: his decisions, not bugs to fix and **not findings
     to report**. Touch a project's config only when he names it. Work needing the master closed waits —
     he closes it and says so. A project of yours that appears there is one he copied to look at: say so
     in a line, do not investigate or delete.
   - **Workers:** author, configure and build freely. One job, then `bin/sqx-worker.sh [--role ROLE]
     stop`. Between start and collect the custodian receives only `-project action=status` (owner,
     2026-09-25) — never `count`, a load or an export: `count` syncs **from** files and wipes what is
     only in memory, which is rule 1 firing (`knowhow/databanks/databank-verbs.md`). The end is `Project
     finished` in SQX's own log. The window's three confirmation-gated launchers start a worker task the
     same way — «Continuar workflow» (owner, 2026-09-27), «Lanzar en SQX» (owner, 2026-09-28) and MT5
     Bridge's «Verificar en SQX y en MT5» (owner, 2026-09-29) — details in `ui/README.md`,
     `ui/daemon/advance/`, `ui/daemon/launch/`, `ui/daemon/mt5bridge/`.
   - **Other sessions share the workers; each install now carries a real owner lock**
     (`OPEN.md` #32, owner 2026-09-29): `start` writes `<install>/user/log/OWNER` (holder —
     `$CLAUDE_CODE_SESSION_ID`, else `--owner`/`$SQX_OWNER`, else "owner" — PID, start time);
     `stop` from a different holder refuses (`--force` overrides it), and a lock whose PID
     is dead and port is down clears itself — but still `ListAgents`, `ls -lt
     <worker>/user/projects | head` and the day's log before touching one. Start and stop
     only through `bin/sqx-worker.sh` or
     `sqx.variants.execute.awake()`, never an ad hoc script — they refuse a second `sqcli` on the same
     install, which would otherwise rewrite its port to the master's.
   - The RAM split is the owner's (125 GB: heaps above, Python 20 GB, OS 10-12). Do not raise a heap
     without redoing it. → `knowhow/perf/ram-budget.md`
4. **Never edit a `project.cfx` a running instance holds** — SQX rewrites the file on save and exit, and
   the change is silently lost. Use the `-project` API on the worker.
5. **Before authoring or modifying any project, task or template:** run `python3 -m core.assets <SYMBOL>`,
   report the overrides applied, and stop if it exits non-zero.
6. **Project names: `Test_<...>` or `Trade_<...>`, underscores only.** The HTTP API splits its command on
   whitespace. `Test_` is a functional test, thrown away when it has answered; `Trade_` is meant to bear
   real fruit (owner, 2026-09-26). The builder refuses any other name and records every project in
   `AlgoData/projects/registry.csv`. **Whoever creates a `Test_` project retires it when the task ends:**
   `python3 -m sqx.projects.retire <P> --role <role> --yes`, worker stopped. The `projectJanitor` agent
   sweeps what was forgotten every Monday at 03:00 (`sqx/projects/sweep.py`).
7. **Heavy data goes to the data root** (`~/Desktop/AlgoData`). Never write data into the repo.
8. **A new command ships with its manual chapter, in the same task — and the owner reads only PDFs.**
   `docs/manual/` holds eleven PDFs, one per workflow family, and nothing else: **no `.md`, no images**
   (owner, 2026-09-26). The chapters and their screenshots live in `AlgoData/manual-fuentes/`
   (`core.paths.MANUAL_SRC`): copy `_PLANTILLA.md` there to `NN-<name>.md`, in Spanish, screenshots of
   real output in its `assets/`, add the stem to a family in `tools/manual.py`, and rerun `python3
   tools/manual.py`. `checks.py` fails on a `__main__` that no chapter names, neither by its path nor by
   its `python3 -m` dotted form. `PENDIENTE.md` there is inherited backlog only — nothing new goes in it.
9. **Writing Python? Read `CODESTYLE.md` first.** No absolute path outside `core/paths.py`. When done:
   `python3 tools/depmap.py && python3 tools/checks.py`.
10. **Every SQX run happens in a CUSTOM PROJECT — never in the stock `Builder` or `Retester`.** Owner,
    2026-09-23. A test on a template, a symbol or a timeframe gets a project of its own, cloned from the
    frozen donor by `sqx/projects/builder.py`, or an existing custom project reused by name. The stock
    projects are not harnesses: they carry someone else's costs, databanks and task chain, and a run
    inside one is unattributable afterwards. Per-task costs are what makes this work — one project holds
    the build on `build` and the retests on `oos1`, each with its own spread, slippage, swap, asset and
    cross-checks. **A workflow run lives in ONE project** (owner, 2026-09-25): `builder --workflow`
    creates every step's task at step 5, and each step switches on only its own before `action=start`,
    which skips inactive tasks (`sqx.projects.stage`; every configurator does it for its step).
11. **Ambiguous? Ask — always.** Owner, "guárdatelo a fuego". When an idea for a strategy or an automation
    admits more than one reading — "crosses above the Keltner": the upper band or the middle line? — list
    the readings and ask which, at every link of the chain (idea → block → group → template → project)
    and before generating anything. Never pick the common reading and carry on: a silent assumption in an
    entry propagates into the build and everything after it, and the CPU it burnt does not come back. In
    a skill, ambiguity is a stop with a question, never a documented default.
12. **One folder, one branch, and the owner commits.** Owner, 2026-09-26. Every session and every agent —
    subagents and the nightly ones included — works in `~/Desktop/AlgoProject` on `master`. Never `git
    worktree`, never `isolation: "worktree"`, never a second clone, never switch or create a branch: git
    is the version control, not the folder. Never commit on your own: a task that changed anything ends
    with the list of files changed and, as its last line, **¿Quieres hacer el commit?** — commit only
    after he says yes, staging only the files of that task (never `git add -A`: other sessions leave their
    own changes in the same tree).

## ROUTER — read only what the task needs

| task | read |
|---|---|
| a fact about formats, the API, exports, conditions, costs, research, perf | `grep -rh '^q:' knowhow/<domain>/`, then read only the card's header (up to `## Evidence`) — domains in `knowhow/INDEX.md` |
| writing or changing Python | `CODESTYLE.md`, then the folder's own `README.md` |
| authoring blocks, groups, templates, projects | `sqx/CLAUDE.md` |
| any study — population or one strategy: where it lives, the shape of a module, the traps | `studies/CLAUDE.md`, then the study's `README.md` |
| how something is computed and shared: pricing, nulls, resampling, regimes, multiple testing | `engines/README.md` |
| where an old path went (`strategies/…`, `tasks/…`, `nulls/`, `gate/`) | `docs/MAPA-DE-CARPETAS.md` |
| portfolios | `portfolio/CLAUDE.md` |
| what a prop firm's account costs with its add-ons, and its rules (the firms of `AlgoData/funding/firms.yaml`; adding one: `/firm-onboard`) | `python3 -m portfolio.funded.catalog.show <firm or plan>`, then `portfolio/funded/catalog/README.md` — refreshed every Sunday by the `fundingWatcher` agent |
| prop-firm discounts: what is on today, and whether one is worth it | `python3 -m portfolio.funded.deals.worth [deal_id]`, then `portfolio/funded/deals/README.md` — hunted daily at 10:00 by the `dealHunter` agent, desktop notification |
| MetaTrader 5: install under Wine, backtest an SQX EA in its tester, compare with SQX, read the terminal (MCP `mt5`, no order tools) | `mt5/README.md`, then OPEN.md #78 |
| step 26: a strategy in SQX at each prop firm's conditions against its MT5 backtest on that firm's account (window › MT5 BRIDGE › Verificar) | `mt5/verify/README.md`, then encargo 34 §0.5 |
| whether a result beats random entry, and which channel the edge lives in | `studies/readings/monkey/README.md` |
| cribar una poblacion OOS entera hasta una lista de supervivientes | `studies/screening/gate/README.md` |
| running something, or explaining to a human how to | the chapter in `AlgoData/manual-fuentes/` (`00-empezar.md`, then that module's); the owner gets the PDF in `docs/manual/` |
| what one SQX project actually does | regenerate on demand: `sqx/inspect/dump_project.py <PROJECT>` (`OPEN.md`) |
| what is broken or pending | `OPEN.md` — read its index at the top, then only the section you need (`grep -n '^## <N>' OPEN.md`); closed issues are in `docs/OPEN-closed.md` |
| **la secuencia entera, de la idea a la estrategia superviviente — los 20 pasos y en cuál estás** | `docs/AgentPDFs/WORKFLOW.md` — manda sobre el orden que digan los otros dos dossiers |
| **what to work on next** | `docs/AgentPDFs/WORKFLOW.md` §«Lo que bloquea hoy», then `OPEN.md` |
| **la ventana de escritorio: la librería de plantillas, su cobertura y el chat que redacta una nueva** | `ui/README.md`, then `docs/manual/02-la-ventana.pdf` (cap. 35-app-plantillas) |
| **los activos: costes, tramos, rangos y doctrina, sin abrir un YAML** | `assets/RULES.md`, then `docs/manual/02-la-ventana.pdf` (cap. 38-app-activos) — la ventana los escribe, `core.assetwrite` es el único escritor |
| what anything costs in time, memory or disk | `docs/manual/03-datos-costes-y-registro.pdf` (cap. 12-rendimiento), then `perf/README.md` |
| what data already exists | `~/Desktop/AlgoData/INDEX.md` |
| **what skills exist, what each is for, and which are candidates to retire** | `docs/SKILLS.md` — generated by `tools/skillmap.py` |
| what the code imports | `docs/DEPENDENCIES.md` |

## Standing rules

**Anything with an interface is a view inside `ui/`** — the PySide6 window over the local FastAPI daemon.
Owner, 2026-09-24: no new `serve.py`, no panel in the browser. The three Flask explorers were retired on
2026-09-25 (encargo 19): a study returns data and the window paints it. A new zone opens in the terminal
style (`theme.T`, a `QFrame` named `term`); do not start a second theme or a second app. Its SQX-launching
buttons are covered by rule 3. → `ui/README.md`

**An analysis ends in a decision, not a description.** "ρ = +0.22 between Sharpe IS and PF OOS" is
unfinished. The result the owner acts on is one of: a filter to set when generating in SQX, a filter to
screen a databank out of sample, the metric the genetic search should optimise, or a list of survivors —
each **with its cost in strategies next to its gain**, and the search space it was picked from. "This
barely helps" is a valid decision; say it plainly. A chain he will run again becomes a skill, not a
procedure re-derived each session.

Found a non-obvious fact? Write it as a card in `knowhow/<domain>/` **in the same task** — edit the card
that exists, never append; format in `knowhow/INDEX.md` — tagged 🔬 tested · 📓 from logs · 🤔 inferred. A
finding left in a transcript dies with the session. If it contradicts this file, fix this file too.

## Layout

`ui/` the desktop app (window + local daemon) · `core/` shared library, and `core/study/` the contract
every study speaks · `sqx/` SQX surface · `studies/` every question asked of a strategy or a population, by
WORKFLOW family · `engines/` what the studies compute with · `portfolio/` portfolios, and the trade-level
Monte Carlo · `pipeline/` one mother in, one verdict out, unattended · `ledger/` the global search ledger
and the frozen thresholds · `perf/` cost catalogue · `mt5/` MetaTrader 5 under Wine and its MCP server ·
`assets/` cost overrides · `knowhow/` facts · `docs/` manual and owner's dossiers ·
`tests/` golden and known-answer tests · `tools/` checks and generators · `bin/` worker scripts · `config/`
machine settings (the real one is not in git) · `scratch/` throwaway, not in git. The agents' daily and weekly
reports (audit, fixes, fondeo, proyectos) live in `AlgoData/audit/` (`core.paths.AUDIT`), not in git.

master `~/Desktop/SQX` (5050) · conductor `~/Desktop/SQX_w1` (5060) · custodian `~/Desktop/SQX_w2` (5070) ·
data `~/Desktop/AlgoData` · machine-specific paths: `config/machine.yaml`.
