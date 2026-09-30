# AlgoProject

Strategy development for MetaTrader 5 prop-firm and real accounts. StrategyQuant X generates and
robustness-tests candidates; Python does the mathematics that decides which of them are real; a
desktop window drives the whole chain and shows its results.

## The sequence

`docs/AgentPDFs/WORKFLOW.md` is the one ordering of the work, from an idea in the chat to a
strategy validated in MetaTrader 5 on each prop firm's account — 26 steps, each with its status and
what blocks it today. In short:

| steps | what happens | where |
|---|---|---|
| 1–6 | idea → block vocabulary → template → cost preflight → a custom SQX project and its build | `sqx/`, `core/assets.py` |
| 7–8 | retest out of sample in SQX, then screen the population down to candidates | `studies/screening/`, `studies/readings/` |
| 9–12 | does the edge survive other markets and other timeframes? | `studies/transfer/` |
| 13–16 | Monte Carlo retests and parameter permutation: what breaks it? | `studies/breakage/` |
| 16.5–19 | variants, walk-forward correlation, CSCV, walk-forward matrix: does optimising buy anything? | `studies/optimisation/`, `sqx/variants/` |
| 20–25 | the joint blind verdict, exposure, conditional map and structure, the stop for MT5, edge per cost | `studies/closing/`, `studies/readings/` |
| 26 | the survivor in SQX at each prop firm's conditions against its MT5 backtest on that firm's account | `mt5/verify/` |
| after | combining survivors, the funded path first | `portfolio/` |

## The folders

| folder | what it is |
|---|---|
| `ui/` | The desktop app — a PySide6 window over a local FastAPI daemon. Template library, projects and their databanks, one strategy's ficha, the running jobs, the search ledger, portfolios and the MT5 bridge. Open it with `bin/algoui` |
| `sqx/` | Everything touching StrategyQuant X: authoring blocks, groups, templates and projects, configuring each workflow task, variants, exports and curation of databanks |
| `studies/` | Every question asked of a strategy or a population, one folder each, grouped by workflow family. Each returns the contract of `core/study/`, and the window paints it |
| `engines/` | What the studies compute with: trade pricing, null models, resampling, regimes, multiple-testing inference, variants |
| `ledger/` | The global search ledger — one line per search that reduced a population — and the thresholds frozen before looking |
| `pipeline/` | One mother strategy in, one verdict out, unattended and resumable |
| `portfolio/` | Combining strategies, separately for funded accounts and real capital; the prop-firm catalogue and discounts |
| `mt5/` | MetaTrader 5 under Wine: backtesting SQX's EAs in its tester, the MCP server over the terminal (no order tools), and step 26 |
| `core/` | The shared library: paths, assets and costs, SQX readers, the study contract |
| `assets/` | Per-asset costs, segments and ranges. Read with `python3 -m core.assets <SYMBOL>` before authoring anything |
| `knowhow/` | The facts that cost time to discover, one card each, tagged tested / from logs / inferred |
| `perf/` | The cost catalogue — what each expensive part takes in time, memory and disk |
| `docs/` | The owner's manual (eleven PDFs in `docs/manual/`), dossiers and encargos, the folder map and the generated dependency map |
| `tests/` · `tools/` · `bin/` · `config/` | Golden and known-answer tests · checks and generators · worker and scheduled-agent scripts · machine settings |

Data never goes in this repository. It lives in the data root, `~/Desktop/AlgoData`, indexed by its
`INDEX.md` — exports, study reports, the ledger, the manual's sources and the agents' reports.

## StrategyQuant X: three installs

| install | port | role |
|---|---|---|
| master `SQX` | 5050 | the owner's GUI; never built on or driven while open |
| conductor `SQX_w1` | 5060 | headless: authoring, queries, exports, short jobs |
| custodian `SQX_w2` | 5070 | headless: one long job at a time, all cores |

Workers are started and stopped only through `bin/sqx-worker.sh`, which holds a per-install owner
lock so that concurrent sessions do not collide. The rules that keep this safe are in `CLAUDE.md`.

## Setting up on a new machine

```bash
cp config/machine.example.yaml config/machine.yaml   # edit the paths for that machine
python3 -m pip install -r requirements.txt
python3 tools/checks.py                              # should be green
```

Nothing else is machine-specific: `core/paths.py` is the only module that knows where anything lives.
Python 3.10 to 3.13; numpy, scipy and arch have no wheels for 3.14 yet.

That covers a machine that only analyses already-exported data. Setting up **StrategyQuant X itself**
— how many installs, cloning the headless workers, the port triples, and the check that stops a
worker being a silent alias of the master — is `docs/SETUP-NEW-MACHINE.md`. MetaTrader 5 under Wine
is `bin/mt5-install.sh` and `mt5/README.md`.

## Windows

The project splits in two, and only one half is tied to Linux.

| half | what it does | Windows |
|---|---|---|
| export and curation | `core/worker.py`, `core/exportdrv.py`, `sqx/export/`, `sqx/curate/` | **no** — they all shell out to `bin/sqx-worker.sh`, which needs `rsync`, `ss`, `curl` and `setsid`. They raise a clear `RuntimeError` instead of failing obscurely |
| analysis | `studies/`, `engines/`, `portfolio/`, over CSVs already in the data root | **yes** |
| the desktop app | `ui/` | **yes**, with no SQX install — `bin\algoui.cmd` |

Set up exactly as above, with forward slashes in `machine.yaml`, and drop the `sqx_workers` and
`strategy_pools` blocks:

```yaml
data_root: C:/Users/<you>/Desktop/AlgoData
sqx_master: C:/none      # required to be present, never opened on Windows
sqx_worker: C:/none
```

`bin\algoui.cmd` sets `PYTHONUTF8=1` before starting the window, and the daemon's jobs get it too:
without it Python on Windows reads and prints in cp1252. With no install, a template's page shows
its bound holes as bound to a group this install lacks — the group names live in the install's
`blockGroups.xml`. Verified on 2026-09-26 by a clean copy of the tree with no SQX path, every zone
walked offscreen; not yet on a real Windows box.

Porting `sqx-worker.sh` to cross-platform Python would remove the split; it is not done.

## Working here

Read `CLAUDE.md` — it holds the rules that prevent irreversible damage, and a router that says which
file to open for which task. Read `CODESTYLE.md` before writing Python, and the folder's own
`README.md`. What is broken or pending is `OPEN.md`; where an old path went (`tasks/`,
`strategies/`, …) is `docs/MAPA-DE-CARPETAS.md`.

Skills (`.claude/skills/`, catalogued in `docs/SKILLS.md`) turn each workflow step the owner runs
again into one command — `/template-run`, `/oos-gate`, `/crossmarket`, `/crosstf`, `/mcretest`,
`/spp`, `/variants`, `/wfm`, `/export`, `/curate`, `/translate` and others. Scheduled agents
(`.claude/agents/`, launched by `bin/`) keep the project honest unattended: a nightly audit,
documenter and fixer, a weekly project janitor, and the prop-firm catalogue watcher and daily deal
hunter. Their reports go to `AlgoData/audit/`. `/sync` keeps this GitHub copy equal to the machine —
see `docs/manual/01-empezar.pdf`.
