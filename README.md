# AlgoProject

A research pipeline for systematic trading strategies, from a published idea to a strategy
validated in MetaTrader 5 on prop-firm and real accounts. StrategyQuant X generates and
robustness-tests candidates; Python does the statistics that decide which of them are real; a
desktop window drives the whole chain and shows its results.

## What it is built around

**Most backtested edges are selection artefacts, so the pipeline is designed to reject.** Every
candidate is judged against a null rather than against zero, and every look at the data is counted:

- **Thresholds frozen before looking.** Each judging step reads its criteria from `ledger/`, set
  before the population exists; a global search ledger records every search that reduced a
  population, so multiple testing is corrected over what was actually tried.
- **Nulls that fit the question.** Random-entry traders with the strategy's own exits and costs,
  joint year-shift nulls for cross-market and cross-timeframe transfer, CSCV for the probability of
  backtest overfitting, stepwise multiple-testing inference over the survivors (`engines/`).
- **Three windows, one of them blind.** Strategies are built on `build`, screened on
  `oos1`, and `oos2` stays reserved for the final joint verdict.
- **Pessimistic costs.** Measured spread per session segment, slippage, and commission and swap at
  the worst of the brokers traded, set per task (`assets/`).

## Automated research, supervised

The chain runs unattended, and a person decides at every point where a decision spends compute or
commits to a result:

| stage | what runs by itself | what the owner decides |
|---|---|---|
| research | a daily scout reads published research and extracts each rule as an entry anchored to verbatim quotes; a market profile measures the entries; a director agent ranks asset × timeframe × direction × family cells and brings three ideas, each attacked by a reviewer agent before any CPU is spent | which proposal to run — a veto in the window; an ambiguous rule is a question, never a silent default |
| workflow | one command creates the project and runs steps 5 to 25 — every SQX task and Python study — judging each step by the frozen criteria and cutting the population itself; a campaign loops it over template × asset × timeframe | every argument of the run, and each launch from the window is confirmation-gated |
| upkeep | nightly audit, documentation and fix agents; a daily commit proposal | the commit — agents propose, they never commit or push |


## The sequence

`docs/AgentPDFs/WORKFLOW.md` is the one ordering of the work, from an idea in the chat to a
strategy validated in MetaTrader 5 on each prop firm's account — 26 steps (plus 10.5, 11.5, 11.7,
16.5 and 18.5), each with its status and what blocks it today. In short:

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

Steps 5 to 25 run through **one command**, never step by step by hand:

```bash
bin/workflow.sh simple   <PROJECT> <SYMBOL> <TF> <long|short> <PALETTE> "<PURPOSE>" <STRATEGIES> <MINUTES>
bin/workflow.sh template <PROJECT> <SYMBOL> <TF> <TEMPLATE.sqx> <PALETTE|-> "<PURPOSE>" <STRATEGIES> <MINUTES>
bin/workflow.sh run      <PROJECT>      # an existing project, from where its rail is
bin/workflow.sh plan     <PROJECT>      # prints what `run` would do, runs nothing
```

It creates the custom project on the custodian and runs every SQX task and Python study in one
session (`pipeline/autopilot/`), judging each step by the frozen `criteria.yaml` and cutting in SQX
instead of stopping. The campaign (`pipeline/campaign/`) loops it unattended over template × asset ×
timeframe. A strategy that passes the gate of step 8 is saved at once in the strategy store
(`core/store/`) — its `.sqx`, every later test's results and its trades — because a genetic build
cannot be reproduced; a project is not retired until its survivors are whole there.

Before step 1 there is a research chain that decides where to look: the literature scout reads
published research into quote-anchored entries, the market profile measures them, and the research
director proposes one asset × timeframe × direction × family cell with three ideas for the owner to
veto (`studies/research/`).

## The folders

| folder | what it is |
|---|---|
| `ui/` | The desktop app — a PySide6 window over a local FastAPI daemon. Template library, projects and their databanks, one strategy's ficha, the running jobs, the search ledger, portfolios and the MT5 bridge. Open it with `bin/algoui` |
| `sqx/` | Everything touching StrategyQuant X: authoring blocks, groups, templates and projects, configuring each workflow task, variants, exports and curation of databanks |
| `studies/` | Every question asked of a strategy or a population, one folder each, grouped by workflow family. Each returns the contract of `core/study/`, and the window paints it |
| `engines/` | What the studies compute with: trade pricing, null models, resampling, regimes, multiple-testing inference, variants |
| `ledger/` | The global search ledger — one line per search that reduced a population — and the thresholds frozen before looking |
| `pipeline/` | The workflow unattended: the autopilot behind `bin/workflow.sh`, the campaign over template × asset × timeframe, and one mother strategy in, one verdict out, resumable |
| `portfolio/` | Combining strategies, separately for funded accounts and real capital; the prop-firm catalogue and discounts |
| `mt5/` | MetaTrader 5 under Wine: backtesting SQX's EAs in its tester, the MCP server over the terminal (no order tools), step 26, the weekly reconciliation against live accounts and the fleet on the VPS |
| `core/` | The shared library: paths, assets and costs, SQX readers, the study contract, the strategy store |
| `assets/` | Per-asset costs, segments and ranges. Read with `python3 -m core.assets <SYMBOL>` before authoring anything |
| `knowhow/` | The facts that cost time to discover, one card each, tagged tested / from logs / inferred |
| `perf/` | The cost catalogue — what each expensive part takes in time, memory and disk |
| `docs/` | The owner's manual (twelve PDFs in `docs/manual/`), dossiers and encargos, the folder map and the generated dependency map |
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

Skills (`.claude/skills/`, catalogued in `docs/SKILLS.md`) turn each chain the owner runs again
into one command — `/workflow-simple` and `/workflow-template` for the whole workflow, `/store-save`,
`/store-open` and `/store-resume` for the strategy store, `/research-direct` and `/literature-scout`
for the research chain, and one per step (`/oos-gate`, `/crossmarket`, `/crosstf`, `/mcretest`,
`/spp`, `/variants`, `/wfm`, `/export`, `/curate` and others) for testing a step on its own. Scheduled agents
(`.claude/agents/`, launched by `bin/`) keep the project honest unattended: a nightly audit,
documenter and fixer, a daily commit proposal at 05:45 (propose only: the owner commits, with one «sí» to `python3 -m tools.commit_apply`), a weekly project janitor, the prop-firm catalogue watcher and daily deal
hunter, the daily literature scout and the weekly MT5 reconciliation. Their reports go to `AlgoData/audit/`. `/sync` keeps this GitHub copy equal to the machine —
see `docs/manual/01-empezar.pdf`.

Two scheduled jobs need no model and so are plain cron scripts, not agents:
`bin/weekly-data-update.sh` (Saturday 02:00) snapshots the master's projects, runs the GUI's
"Update all" on SQX's data headless, refreshes each asset's data range in `assets/_policy.yaml` and
the brokers' commissions; `bin/monthly-oos2-roll.sh` (Saturday 02:05, acts only on the month's
first Saturday) waits for that update and moves every decided `oos2` to end on the last day of the
previous month. Both log to `AlgoData/logs/`.
