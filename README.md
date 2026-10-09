# AlgoProject

A research pipeline for systematic trading strategies: from a rule in a published paper to a
strategy validated in MetaTrader 5 on prop-firm and real accounts. StrategyQuant X searches the
strategy space and re-runs backtests; Python does the inference that decides which results are
real; a desktop window drives the chain and shows every verdict.

The premise is that **a backtest is a search result, and most search results are selection
artefacts**. So the pipeline is built to reject: every candidate is judged against a null generated
for that question, every search that narrowed a population is counted, and the last data window is
opened once.

## Design principles

- **A null per question, not a threshold on a metric.** "Profit factor above 1.3" says nothing
  about what chance produces on the same market with the same costs. Each judging step states its
  null and reads a z or a p against it.
- **Three windows.** The builder sees only `build`. The out-of-sample retest and the robustness
  steps read `oos1`. `oos2` is reserved by name for the six studies of the final stage
  (`assets/_policy.yaml`) and rolls forward monthly. For gold: 2008–2017 · 2018–2022 · 2023–today.
- **Thresholds are data with an author and a date.** They live in `pipeline/autopilot/criteria.yaml`
  and `ledger/thresholds.yaml`, every change is appended to a history file, and each rule returns
  *pass*, *limbo* or *fail* — a missing fact is limbo, never a pass.
- **The search is counted.** `ledger/` holds one line per search that reduced a population; the
  trial count N and the cross-trial dispersion pooled from it feed the deflated Sharpe ratio.
- **Costs are pessimistic and per task.** Spread is the widest broker's time-weighted mean as a
  percentage of price, slippage 35 % of it, commission and swap the worse of the firms traded
  (`assets/RULES.md`). The nulls pay the same costs as the strategy.
- **Excess, not return.** Results are read as excess over the market's own drift rather than as
  raw return.

## The sequence

`docs/AgentPDFs/WORKFLOW.md` is the one ordering of the work — 26 steps (plus 10.5, 11.5, 11.7,
16.5 and 18.5). What each stage asks, and against what:

| steps | question | statistic and null | where |
|---|---|---|---|
| 1–6 | what to build | an idea becomes block vocabulary, a template, a cost preflight and a custom SQX project; at most two entry and two exit conditions, one direction, no clock blocks | `sqx/`, `core/assets.py` |
| 7–8 | does a build-selected strategy survive `oos1`? | a 16-rule cascade: t of the excess over drift, z against a **windowed random-entry null** (each trade re-entered at a uniform bar of the calendar window it opened in, ATR-sized, costs charged; 5,000 draws), a homogeneity permutation test, a block-bootstrap drawdown test | `studies/screening/gate/`, `engines/nulls/` |
| 9–12 | does the logic travel to other markets and timeframes? | z of the real run against 5,000 runs of the same trades **shifted by whole weeks inside each calendar year**, one shift per year shared across markets, so cross-market dependence is kept in the null | `studies/transfer/` |
| 13–16 | what breaks it? | ~1,000 SQX re-runs of the whole backtest per perturbed input; retention of the excess, attribution under Benjamini–Yekutieli; System Parameter Permutation as a map, never a filter | `studies/breakage/` |
| 16.5 | is the parameter surface a plateau or a spike? | variants from a Latin-hypercube design; Sobol indices of a fitted quadratic surface against a shuffled-metric R² | `sqx/variants/`, `studies/optimisation/cloud/` |
| 17 | does in-sample rank predict out-of-sample rank? | Spearman ρ of IS against OOS excess over the variants, against a weekly sign-flip null | `studies/optimisation/wfc/` |
| 18 | how likely is the selection to be overfit? | **CSCV** (Bailey, Borwein, López de Prado, Zhu): 16 blocks, 12,870 partitions; PBO and P(loss) read against their own null's 95th percentile (stationary bootstrap of weeks). It can discard and never confirms | `studies/optimisation/cscv/` |
| 18.5–19 | is the variant order stable across markets, and does re-optimising pay? | Spearman ρ of variant order across markets; a 30-cell walk-forward matrix, median net `oos2` excess against a shared-sign weekly flip null | `studies/optimisation/` |
| 20 | the joint blind verdict on `oos2` | Hansen's **SPA** and Romano–Wolf's **StepM** against buy-and-hold, Politis–White block length | `studies/closing/blindJoint/`, `engines/inference/snooping/` |
| 21–25 | what is the survivor made of? | return per unit of market time at equal risk; a conditional map over volatility × trend terciles; ablation and inversion of each entry condition; the stop from the MAE distribution of in-sample winners; edge per unit of cost. Descriptive — none of these selects | `studies/closing/`, `studies/readings/` |
| 26 | does MetaTrader 5 agree? | the strategy priced in SQX at each prop firm's conditions against its MT5 tester run on that firm's account, trades paired by entry time | `mt5/verify/` |
| after | combining survivors | prop-firm rules simulated on floating equity rebuilt from M1 wicks (MAE/MFE), a trade-level Monte Carlo, and the expected value of a bank of funded accounts | `portfolio/` |

Shared machinery lives in `engines/`: i.i.d. and stationary bootstraps and block shuffles
(`resample/`), the random-entry nulls (`nulls/`), weekly sign-flip nulls (`weekly/`), volatility
regimes by ATR or GARCH(1,1) terciles (`regimes/`), and Benjamini–Hochberg, Storey's null share,
SPA and StepM (`inference/`). PSR, MinTRL and the deflated Sharpe follow Bailey–López de Prado.

### What is not settled

Stated here because it is the first thing a reader should ask:

- The thresholds of steps 10 and 14 are marked provisional and uncalibrated in `criteria.yaml`.
- Under the current provisional rule, step 20's verdict is the worst state of steps 17–19; SPA and
  StepM are computed and shown, and decide nothing yet.
- The deflated Sharpe is fed the dispersion inside one mother's variants, which is narrower than
  the whole study's and errs in the flattering direction (`ledger/README.md`).
- The `oos2` reservation is enforced in code for autonomous agents; a person can still read it.
- `portfolio/` has run only on a test pool: there is no live portfolio result yet.

## Research before the search

Where to point the builder is itself a multiple-testing problem, handled before any strategy
exists (`studies/research/`):

- **Literature** — a daily scout reads arXiv q-fin and OpenAlex, rejects each paper by nine hard
  filters with the sentence that shows why, and extracts each surviving rule as an entry whose
  fields are anchored to quotes verified verbatim against the stored source.
- **Market profile** — 19 assets × four timeframes × long/short × seven idea families: 14,364
  tests on `build` only, each against block-resampled series, Benjamini–Hochberg over all of them.
  A cell must be significant, pay twice its cost, be stable across the build years and trade
  enough.
- **Power** — an edge of known size is planted and put through the profile's own test, which gives
  the power curve and the minimum detectable effect: what an empty cell does and does not rule out.
- **Pooling** — per asset group, a Stouffer sum of each asset's z against a joint resampling null,
  with DerSimonian–Laird shrinkage.
- **Board** — cells ranked by prior, evidence, signal, gap and past results; a director agent picks
  one and brings three ideas, each attacked by a reviewer agent before any CPU is spent.

## Automated, supervised

Steps 5 to 25 run through one command, in one SQX session:

```bash
bin/workflow.sh simple   <PROJECT> <SYMBOL> <TF> <long|short> <PALETTE> "<PURPOSE>" <STRATEGIES> <MINUTES>
bin/workflow.sh template <PROJECT> <SYMBOL> <TF> <TEMPLATE.sqx> <PALETTE|-> "<PURPOSE>" <STRATEGIES> <MINUTES>
bin/workflow.sh run      <PROJECT>      # an existing project, from where its rail is
bin/workflow.sh plan     <PROJECT>      # prints what `run` would do, runs nothing
```

The autopilot (`pipeline/autopilot/`) runs every SQX task and Python study, judges each step by
the criteria file and cuts the population in SQX itself; the campaign (`pipeline/campaign/`) loops
it over template × asset × timeframe. A strategy that passes step 8 is saved at once in the
strategy store (`core/store/`) with every later test's results and trades — a genetic build cannot
be reproduced.

A person decides wherever a decision spends compute or commits to a result:

| stage | runs by itself | the owner decides |
|---|---|---|
| research | scout, profile, board, the director's proposal and its adversarial review | which proposal to run; an ambiguous rule is a question, never a silent default |
| workflow | project creation, every task and study, every cut | every argument of the run; each launch from the window is confirmation-gated |
| upkeep | nightly audit, documentation and fix agents; a daily commit proposal | the commit — agents propose, they never commit or push |

Known-answer and golden tests (`tests/`, 270+ files) pin the statistics: planted edges that must be
found, no-edge panels that must reject at the nominal rate, and SQX file formats read back exactly.

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
