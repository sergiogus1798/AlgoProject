# Portfolio construction engine — implementation plan

Written 2026-09-30 for the agents that will build it. Nothing here is built. Read `portfolio/CLAUDE.md`
(settled decisions — final), `portfolio/DECISIONS.md` (open — do not answer them) and
`BUILD_COMPENDIUM.md` first; this file assumes them. Every question in §12 is a **stop**: a
milestone blocked by one does not start with a guessed default (root `CLAUDE.md` rule 11).

Tags: 🔬 verified by the session that wrote this, with the file that proves it · 🤔 inferred, not
tested.

---

## 1 · Facts this plan stands on

| fact | source |
|---|---|
| 🔬 SQX stores per strategy each trading day's **lowest equity** (`dailyEquity.bin`: closed P&L + open positions at their worst M1 wick, cumulative, feed clock) — **not** a mark to market (corrected 2026-09-30: the M1 rebuild matches it on 100 % of 3,983 days, max 0.16 $); only the `Main` result matches net profit. A daily MTM P&L exists only from the rebuild | `knowhow/sqx-format/daily-equity-bin.md`, parser `core/sqxstats.py` `equity()` |
| 🔬 The archive freezes that curve as `harvest/equity.parquet` (`day, identity, equity, sample`) and the trades as `harvest/trades.parquet` (orderstocsv schema + `identity, sample`) | `AlgoData/archive/4d679e…/2026-09-28T0919/harvest/`, `core/archive/README.md` |
| 🔬 **The archive holds only `IS` and `OOS` (= `oos1`)** — the gate's cosecha. The one archived strategy: IS 2007-12-03…2017-12-28, OOS 2017-11-30…2022-12-29; **no `oos2` at all** | same parquet, read 2026-09-30 |
| 🔬 A mother that reached step 16.5 has its **full-history daily-low curve** (build, oos1, oos2) as column `P00000` of its variant batch's `equity.parquet`, 2007-12-03…2026-08-27 on USDJPY — but the archive does not freeze the batch | `AlgoData/strategyPermutations/<P>/<mother>/equity.parquet`, `knowhow/sqx-format/leg-curve-warmup.md` |
| 🔬 Every leg's curve opens ~2 months early with zero P&L, so legs overlap and dates repeat (41 duplicates in the batch above). Slice by `core.assetdata.window()`, never by the curve's own splits | `knowhow/sqx-format/leg-curve-warmup.md`, `core/assetdata.py:155` |
| 🔬 Segments differ per asset: FX and XAUUSD build 2008-2017 / oos1 2018-2022 / oos2 2023-2026-08-30; indices build 2011-13…2019 / oos1 2020-2023 / oos2 2024-2026-08-31; BRENT, XAGUSD, SP500ft undecided | `assets/_policy.yaml` `segments:` |
| 🔬 M1 bars: `AlgoData/bars/<feed>/M1.parquet`, read by `core.barstore.source(feed, columns)`; float64, indexed by bar-open time | `core/paths.py:184`, `core/barstore.py:65` |
| 🔬 Trade and bar times are **naive, in the feed's broker clock**: Infinox `EET`, the5ers `Asia/Jerusalem`, `UKOIL.cash_M1` `EETUS` (= New York + 7 h, no IANA name); `sqx.inspect.feeds.timezone(feed)` reads it | `knowhow/export/feed-clock-timezones.md`, `sqx/inspect/feeds.py:10` |
| 🔬 `Profit/Loss` is account money **net** of commission and swap, at each trade's own `Size`, and `Size` varies trade to trade (SQX's money management) | `knowhow/export/orderstocsv-schema.md`, `knowhow/research/per-trade-usd-conflates-sizing.md`, `core/trades.py:28` |
| 🔬 Point value: measured from the trades (`engines.market.calibrate.point_value`, 99.85 vs 100 on gold) or read from `assets/symbols/<S>.yaml:instrument.point_value` | `engines/market/calibrate.py:44` |
| 🔬 Nothing in the project rebuilds floating equity from trades + bars; the one trades-to-daily function (`studies/closing/exposure/benchmark.py:daily`) books P&L on the close day | Explore sweep, 2026-09-30 |
| 🔬 SQX's curve vs its own net profit differs by up to a few trades when a position is open at a window boundary — the tolerated noise floor | `sqx/variants/curves.py:20` `PLAUSIBLE_TRADES = 3` |
| 🔬 The ledger writes **one row per search**, not per candidate; the candidates' scores go in `scores` so `n_scored` and the pooled sigma count them. Required: `step, launched_by, symbol, timeframe, segment, n_in, n_out, criterion` | `ledger/record.py:11,33,85`, `ledger/README.md` |
| 🔬 A ledger study is `(symbol, timeframe, family)`; a multi-asset portfolio has no natural study id | `ledger/study.py:21` |
| 🔬 The WFC/CSCV pattern: ask `gate.allow` for every segment **before** opening data, then one row per segment read | `engines/variants/look.py:32,68` |
| 🔬 The ledger door binds only an autonomous agent (`ALGO_AUTONOMOUS=1`); a human may read any segment, and the row is written either way | `ledger/gate.py:40-66` |
| 🔬 The archive has **no development/validated mark**; `manifest.json` has `step` (e.g. `"16.5"`) | `core/archive/manifest.py`, manifest read 2026-09-30 |
| 🔬 A study returns the contract dict (8 block kinds, 5 states); the window paints it with `ui/desktop/blocks/` | `core/study/CONTRACT.md` |
| 🔬 Long jobs go through `sqx/jobs.py`: lane `python` (core-budgeted, refuses below 20 GB free RAM) or `conductor` (SQX) | `sqx/jobs.py:25-30,88` |
| 🔬 Python's RAM reserve is 20 GB; the worst catalogue target peaks 2.5 GB | `knowhow/perf/ram-budget.md` |
| 🔬 `checks.py`: 500 lines per file, README table per folder, docstrings + type hints, no absolute path outside `core/paths.py`, every `__main__` named by a manual chapter, pinned requirements, fresh `DEPENDENCIES.md` | `CODESTYLE.md`, `tools/checks.py` |
| 🔬 `docs/manual/` was ten PDFs, one per family (`tools/manual.py` `FAMILIES`); the eleventh, «11-cartera», added 2026-09-30 (Q17) | `tools/manual.py:26` |
| 🔬 AlphaForge filters with `abs(corr) <= threshold` — a strongly **negative** correlation is rejected too | AlphaForge `generator/filters.py:148,161,194` |
| 🔬 AlphaForge's HRP writes each weight at the strategy's position in the dendrogram order and then zips with the names in the original order: weights land on the wrong strategies | AlphaForge `generator/weighting.py:189-193,247` |
| 🔬 AlphaForge: <6 overlapping months → correlation and co-loss stored as `0.0` and the filter passes | AlphaForge `universe.py:123,169`, `filters.py:182,208` |
| 🔬 AlphaForge's `run_expandPortfolio.py` is **not** marginal contribution: pairwise-compatible subsets enumerated exhaustively, ranked by the same 0.8/0.1/0.1 fitness | AlphaForge `run_expandPortfolio.py:198-264` |

## 2 · Scope and the two hand-offs

```
 archive ──▶ POOL (declared, frozen) ──▶ [encargo 33: prohibitions per firm] ──▶ admissible pool
    │                                                                               │
    ▼                                                                               ▼
 UNIVERSE: daily MTM per strategy ─▶ PAIRS (build) ─▶ SEARCH (build) ─▶ WEIGHTS (build) ─▶ VERDICT (oos1, then oos2)
                                                                                          │
                                                        hand-off package ◀────────────────┘ ──▶ encargo 33
```

**In:** layers 1-6 of the brief. **Out, encargo 33's:** risk per trade, sizing, P(pass), prop-firm
rules, Monte Carlo sizing, the firm's server-day translation of the *portfolio* path.
⚠ **Amended by §14 (2026-09-30):** for funded accounts the engine itself chooses by P(pass) on
`build`, calling encargo 33's rule functions; §2.2's hand-off then carries one portfolio per plan.

### 2.1 Hand-off IN — the firm-prohibition filter (encargo 33 → engine)

The engine never decides what a firm forbids. It reads a file encargo 33 writes:
`AlgoData/portfolio/prohibitions/<firm>.csv` with columns
`identity, version, firm, plan, rule, reason, decided_on`. A run takes `--firm <firm>` (or none,
for `real/`), drops every identity listed for that firm **before** the pool is hashed, and reports
`n_pool`, `n_prohibited` and the rows in its result. `n_in` of the search's ledger row is the pool
**after** prohibitions. Until encargo 33 exists, the file is hand-written for the tests only.

Built 2026-10-05 (M6, `inputs/pool.py`): `--firm` on `universe`, `real` and `funded` (there it must
be the plan's firm; `funded_b` inherits it from the stage-A manifest). A strategy that breaks a
plan's rule is **dropped from that plan's pool, never modified** (owner, encargo 33 §6.2). The firm
and plan are part of the config fingerprint, so a filtered pool has its own universe folder. Format
for whoever writes the file: `AlgoData/portfolio/prohibitions/README.md`. 🤔 **Reading of the `plan`
column, the owner's to confirm:** empty = every plan of the firm; otherwise a prefix of the plan key
(`hantec:express` covers every size of Express); a command given a firm and no plan (`universe`,
`real`) applies every row of the firm.

### 2.2 Hand-off OUT — what encargo 33 receives

`AlgoData/portfolio/runs/<run_id>/handoff/`:

| file | contents |
|---|---|
| `portfolio.json` | `run_id`, pool name + hash, firm (or null), members `[{identity, version, symbol, timeframe, feed, clock}]`, `weights {identity: w}` and the weight method, the verdict label and its decision sentence, ledger study + N at run time, `relaxed` flag and which thresholds were relaxed, `development: true/false` |
| `daily.parquet` | members' daily MTM P&L, long form `day, identity, pnl, segment, source` (`sqx` or `rebuild`), in the engine's reference clock (Q4) |
| `trades.parquet` | members' trades, orderstocsv schema + `identity` — so encargo 33 can re-day them on the firm's server clock with the same rebuild function (§5.1), and run its trade bootstrap |

Encargo 33 imports `portfolio.common.construct.equity.marktomarket` to re-day; the engine does not
know any firm's clock.

## 3 · Module layout

Everything new lives in `portfolio/common/construct/` — both destinations use it (`portfolio/CLAUDE.md`:
same pool for funded and real). It mirrors `portfolio/common/monteCarlo/`: one folder per boundary
of `CODESTYLE.md` §5, the orchestrator files at the top. `funded/` and `real/` get nothing in this
plan except the prohibition file format above.

```
portfolio/common/construct/
  config.yaml        every knob (§5.7)
  tooltips.py        one Spanish sentence per knob, for the window's drawer
  inputs/            CONFIGURATION — what the run is run on
    config.py        load config.yaml, ledger:<key> fill, --set overrides → dict
    pool.py          the declared pool: read pools/<name>.csv, drop prohibitions, hash it
    source.py        one archived strategy → {trades, sqx_daily, feed, clock, segments, identity, version, step}
  equity/            EXECUTION — the universe
    clock.py         naive feed clock → reference clock; EETUS as NY+7 h; DST ambiguity counted, never guessed
    marktomarket.py  trades + M1 closes → daily floating P&L per strategy (§5.1)
    reconcile.py     rebuild vs SQX's daily curve → gap per strategy; the licence to use the rebuild
    matrix.py        per-strategy series → daily (days×N) and monthly (months×N) matrices + segment masks
  pairs/             MODELLING (definitions) + EXECUTION (pool-wide)
    measures.py      pure functions on two aligned series; the MEASURES registry (§5.2)
    rolling.py       rolling-window correlation, whole and recent maxima
    stress.py        stress-day correlation and effective number of independent strategies
    table.py         every measure over every pair of the pool → pairs.parquet (chunked)
  search/            EXECUTION under a model — reads the build slice only
    admissible.py    thresholds + pairs table → compatibility graph and the failing filter per pair
    objective.py     the build score of one combination; OBJECTIVES registry (Q10)
    greedy.py        greedy independent-set seeding
    genetic.py       GA operators and loop, pure functions over index arrays
    admission.py     marginal-contribution admission of candidates to a fixed base
    trials.py        the evaluated-combination log and the ledger rows (§6)
  weights/           MODELLING — the pluggable submodule
    __init__.py      REGISTRY {name: fn}; fn(build_daily: DataFrame, cfg) -> dict[identity, float]
    equal.py         1/K — the only method `weights.method` accepts, the mandatory baseline
    risk_parity.py, min_variance.py, hrp.py   M8: 1/σ · minimum variance on the Ledoit-Wolf covariance · HRP (AF's bug fixed)
  verdict/           INFERENCE — judges oos1, then oos2 once; never imports search/ or equity/
    metrics.py       window-robust metrics of one daily P&L path (§5.5)
    null.py          the reference the portfolio must beat on oos1 (Q11)
    deflate.py       the oos2 reading: Sharpe against the expected maximum of the ledger's N
    hold.py          did the diversification hold out of sample
    decide.py, decide_real.py   the decision and its sentence, with the cost next to the gain
  contract/          the result as the contract's blocks, tabs in Spanish
    tabs.py, words.py
  real.py            the real path's search on build (M3); no `run.py` was built — `report.py` orchestrates
  segment.py         a combination's path on one segment at build's weights (what the verdicts read)
  oos2.py            the ONE read of oos2 per pool: stored reading / refusal / gate / deflation / ledger row
  many.py            many.run(inputs, cfg) -> contract dict: the real verdict (a portfolio run is a population result)
  funded_verdict.py  the funded verdict (F4): oos1 against the selected null, then oos2.py
  handoff.py         the hand-off package of §2.2 in <run>/handoff/
  report.py          THE COMMAND: python3 -m portfolio.common.construct.report --pool <name> [--firm F] [--run <run>] [--set k=v]
  candidates.py      THE COMMAND: python3 -m portfolio.common.construct.candidates — prints archive commands, runs none (M0)
  walkforward.py     M8, pure: the test windows of oos1, each method's fixed and re-estimated path, the paired bootstrap against equal
  wf.py              THE COMMAND (M8): python3 -m portfolio.common.construct.wf --pool <name> (--run <run> | --members a,b,c) --set wf.confidence=…
  incubation/        M9: the record of a judged portfolio, the row contract of its fresh days, the reading against the band
    record.py, band.py   register/load/validate · the band of equal-length windows of its own history
    run.py           THE COMMAND (M9): python3 -m portfolio.common.construct.incubation.run register|read — incubation is NOT running
```

**Imports, checked against `docs/DEPENDENCIES.md` and `CODESTYLE.md` §5:**

| layer | may import |
|---|---|
| `inputs/` | `core.archive.read`, `core.assetdata`, `core.paths`, `ledger.thresholds`, `core.study.config` |
| `equity/` | `inputs/`, `core.barstore`, `core.trades`, `engines.market.calibrate`, `sqx.inspect.feeds` (read-only timezone lookup; 🤔 the portfolio tree imports no `sqx.*` today — freeze the zone in the universe manifest so later runs need not) |
| `pairs/` | `equity/matrix` output only (data, not code), numpy/scipy/numba |
| `search/` | `pairs/`, `weights/`, `ledger.record`, `ledger.study`, `ledger.gate` |
| `weights/` | nothing inside the module |
| `verdict/` | `inputs/`, `weights/` (to apply), itself — **never `search/`, never `equity/`** |
| `contract/` | everything above, `core.study` |
| `run.py`, `many.py`, `report.py` | everything |

No `studies.*`, no `ui.*` (`studies/CLAUDE.md`; the archive's `ui` import is its own documented
exception). No new third-party library: numpy, pandas, scipy, numba, pyarrow are pinned
(`requirements.txt`).

## 4 · Data shapes, where they live, what they weigh

New in `core/paths.py`: `portfolio_dir() -> DATA / "portfolio"` (the only path added; rule 9).

```
AlgoData/portfolio/
  pools/<pool>.csv                  identity, version, development, added_on, added_by, note   ← declared before looking
  prohibitions/<firm>.csv           §2.1, written by encargo 33
  universe/<pool_hash>/             a cache: deletable, rebuilt from the archive
    daily.parquet                   day × identity, float64 P&L, NaN outside the strategy's history
    daily_sqx.parquet               the same from SQX's curve, for reconciliation
    monthly.parquet                 month × identity
    reconcile.csv                   identity, corr_daily, max_cum_gap, gap_in_trades, verdict
    pairs.parquet                   i, j, measure, segment, value, n_overlap, state
    manifest.json                   pool hash, config hash, clock per feed, code_version, built_at
  runs/<YYYY-MM-DDTHHMM>_<pool>[_<firm>]/
    result.json                     the contract dict the window paints
    search.parquet                  one row per combination evaluated: members (sorted int16 list), build score, origin (seed/ga/admission), generation
    verdict.csv                     identity, verdict — one row per member
    manifest.json                   pool, firm, prohibitions dropped, config + overrides, relaxed thresholds, ledger rows written
    handoff/                        §2.2
```

Sizes (float64 unless said; days ≈ 4,900 trading days 2007-12…2026-08, 🔬 5,018 rows in the batch
above; months ≈ 225):

| object | N = 50 | N = 500 | note |
|---|---|---|---|
| trades in RAM, all strategies | ~15 MB | ~150 MB | ~2,000-5,000 trades × 14 cols each (🔬 2,094 on the archived one) |
| M1 closes of one feed | ~140 MB | ~140 MB | 8.7 M bars × (time + close); **one feed at a time**, strategies grouped by feed |
| daily matrix (+ SQX copy) | 4 MB | 40 MB | |
| monthly matrix | < 0.1 MB | 1 MB | |
| pairs table | 1,225 pairs × ~12 values ≈ 0.2 MB | 124,750 pairs × ~12 ≈ 15 MB | only the maxima of rolling windows are kept |
| rolling windows, transient | ~1 MB | ~80 MB per measure, chunked to ≤ 64 MB | 🤔 ~160 60-month windows per pair over a 10-year build |
| search log | 30,000 evaluations ≈ 1-2 MB | same | GA 300 × 100 + seeds; size does not grow with N |
| **peak** | **< 0.5 GB** | **< 1 GB** 🤔 | far inside the 20 GB Python reserve; confirm with the perf target |

Time 🤔: the rebuild is dominated by reading M1 (0.4 s per feed, `knowhow/export/exits-and-m1-library.md`);
the pairs table at N = 500 is ~125k pairs × rolling Spearman — minutes in numba, seconds in numpy
for Pearson; one GA evaluation (sum K columns over ~2,500 build days + metrics) is tens of µs.

## 5 · The layers

### 5.1 Universe — daily mark-to-market equity

Two sources, one frame. Which one is authoritative is **Q3**; the plan builds both because
reconciliation needs both.

- **SQX's curve** (`sqx_daily`): `harvest/equity.parquet` (IS + oos1) or a frozen full-history leg
  (Q2). Cumulative → daily by differencing *per leg*, legs cut at the policy's dates
  (`core.assetdata.window`), warm-up zeros and duplicate dates dropped (`leg-curve-warmup.md`).
- **The rebuild** (`marktomarket.py`), for one strategy:
  1. Day boundaries `b_d` in the reference clock (Q4). For each `b_d`, the M1 close of the last bar
     that opened before `b_d` — the price at the label's own instant, never `resample("D").last()`
     (`daily-equity-bin.md`).
  2. For each trade and each boundary strictly inside `(open, close)`:
     `floating_d = side × (P(b_d) − open_price) × size × point_value`.
  3. Daily P&L of a trade: `floating_d − floating_{d−1}` on the days it is open; on its close day,
     `Profit/Loss − floating_{last}`. **The realised P&L anchors the close**, so the sum of a
     strategy's daily P&L equals the sum of its `Profit/Loss` exactly, whatever the point value's
     error on a JPY cross (🤔 its money value per point moves with USDJPY; the anchor absorbs it).
  4. Swap accrues inside `Profit/Loss` at the close, not night by night (🔬 `cost()` recovers it only
     in aggregate): floating equity on held nights omits it. State it in the result; do not model it
     here.
  - Output: a daily series per strategy, `NaN` before its first segment and after its last.
- **Reconciliation** (`reconcile.py`): on every strategy, rebuild vs SQX daily curve over the window
  both cover: daily correlation, max |cumulative gap|, gap in units of the strategy's median |trade|.
  Tolerance starts at SQX's own noise floor — `PLAUSIBLE_TRADES = 3` — and is a knob; a strategy
  outside it is shown in red and left out of the pool until someone looks (never silently kept).
- **Matrices** (`matrix.py`): stack to `days × N`. A day where a strategy has no position and its
  history covers the day is **0**; a day outside its history is **NaN** (AlphaForge filled everything
  with $0 — that is what made "no overlap" read as "uncorrelated"). Monthly = sum over the month,
  NaN when the whole month is outside history. Segment masks per strategy per day from its own
  asset's policy (Q1 decides how masks combine across assets).

### 5.2 Pairwise filters

All computed on the **build** slice only (the combination is chosen reading only `build`;
`portfolio/CLAUDE.md`). Every threshold is a knob, default 0.30 (owner, 2026-09-29).

| measure | definition (to confirm where marked) | from |
|---|---|---|
| Pearson | on aligned monthly P&L (Q7: monthly, daily, or both) | AF, port |
| Spearman | same, ranks | AF, port |
| co-loss | share of overlapping months where both lose: `((a<0)&(b<0)).sum() / n_overlap` | AF `universe.py:154-176`, port |
| tail | Pearson on the months where **either** is below its own 30 % quantile | AF `filters.py:164-194`, port; ⚠️ AF's `correlation_deep.py` uses another definition — do not port that one |
| rolling 60 m, whole | max over every 60-month window (one-month step) of Pearson and of Spearman | AF `filters.py:96-133,258-292` |
| rolling 60 m, recent | same maximum over the windows ending in the recent stretch (Q9: its length; AF 3 years) | AF |
| stress-day | Pearson on stress days only (Q15: which days) | compendium §4.2, new |
| effective N | per candidate set, calm and stress (Q15: formula) | compendium §4.2-4.3, new |
| overlap | number of overlapping months (days for daily measures) | new — AF's `< 6 → 0.0` is fixed |

- **Too little overlap is never 0.0.** Below `min_overlap_months` a pair's state is `insufficient`,
  and Q8 decides whether `insufficient` rejects the pair or passes with a flag counted in the result.
- **Sign** (Q6): AF rejects `|ρ| > 0.30`, which throws away hedges. Not decided here.
- **Relaxed**: `relaxed: {pearson: 0.45, …}` in `--set`. A run whose thresholds differ from the
  ledger's defaults carries `relaxed: true` and the list, on the result's first line and in
  `portfolio.json`; the window paints it `watch`.
- **No same-asset conflict filter** (owner, 2026-09-29): AF `universe.py:179-237` and
  `filters.py:214-253` are not ported.

### 5.3 Combination search

Reads the build slice, the pairs table and the admissible graph. Never sees oos1/oos2: `run.py` hands
it `matrix.slice(build)` and nothing else (test §8.4).

- **Admissible graph**: edge `i—j` when every measure passes. A combination is admissible iff it is a
  clique. The failing filter per pair is kept, so the result can say "de 1.225 parejas, 300 caen por
  co-loss…".
- **Greedy independent-set seeding** (AF `genetic.py:416-554`, rewritten as functions): shuffle,
  add each strategy compatible with every one already in, stop at `k_max`. `seeds` starting sets.
- **GA** (AF `genetic.py`, rewritten): tournament, union crossover, swap/add/remove mutation, every
  filter a hard constraint (children that are not cliques are repaired by dropping the worst-scoring
  offending member, or discarded — 🤔 AF discards; keep that), elitism, early stop on stagnation of
  the **absolute** score (AF tracks it separately from the renormalised one; keep the absolute only).
  Parameters: AF's defaults (300 × 100, elite 0.20, tournament 4, crossover 0.80, mutation 0.40,
  stagnation 10) as knobs, `set_by: AlphaForge` until the owner changes them.
- **Size of a combination**: no `k_min`/`k_max` knob. **`DECISIONS.md` #2, decided 2026-10-04:** the
  funding economics sets it — a member whose smallest trade is under the minimum lot on the 10k
  account at the top of the risk grid is out; K runs from 1 to the largest admissible combination.
- **Objective on build** (`objective.py`, **Q10 = (a), 2026-10-04**: the mean of the signed ranks of
  RAR %, R-cubed, gain-to-pain and P(losing year), taken in a reference set fixed for the run):
  replaces AF's pool-normalised 0.8/0.1/0.1 (the
  compendium marks it [AF✗]). Whatever the owner picks, it is an absolute number (comparable across
  runs and generations) computed on the equal-weighted combination.
- **Marginal-contribution admission** (`admission.py`, a second mode, `--mode admission --base <run_id>`):
  given a base portfolio, a candidate enters iff it is pairwise-admissible against every member and
  its increment to the build objective (Euler decomposition for Sharpe, compendium §3.2) is > 0; the
  expected increment is written before the verdict reads anything, the realised one after. AF's
  exhaustive subset enumeration is the fallback for small candidate lists (≤ 20), under the same
  rule. **Q16 = (c), provisional, 2026-10-04**; the increment's two readings are a required knob
  (`real.increment`: `finite`, owner 2026-10-05). Built as `real.py --base <run folder>`, not
  `--mode admission`; several candidates enter in sequence (owner, 2026-10-05; §12, reading 4).
- **Exhaustive** when the admissible space is small (`C(clique count)` ≤ `exhaustive_max`), as AF's
  `sampler.py` does; otherwise GA.

### 5.4 Weights

`weights/__init__.py`: `REGISTRY = {"equal": equal.weights}`; signature
`fn(build_daily: pd.DataFrame, cfg: dict) -> dict[str, float]`, sum 1, non-negative. Chosen on
build only. The README's table says, per method, what it holds fixed and what it estimates
(`CODESTYLE.md` §5). What a weight multiplies — the P&L as SQX sized it, or a risk-normalised P&L —
is **Q5**. Later methods (min-variance with Ledoit-Wolf shrinkage, risk parity, HRP with AF's bug
fixed, Carver handcrafting) are one file and one row each, and must beat equal weight on OOS through
AF's `wf.py` weight walk-forward (port as the test) before they may be selected — milestone M8.

**Built 2026-10-05** (`wf.py`, `walkforward.py`; chapter 103). Risk parity (1/σ), minimum variance
on the Ledoit-Wolf (2004) covariance and HRP are in `REGISTRY`; **Carver handcrafting is not built**
(its grouping thresholds and its diversification multiplier are undecided). Estimation is `build`,
the test is `oos1` only (`oos2` is never opened), cut in windows of `wf.step_years` from oos1's
first day. Each method walks two arms — `fixed` (the weights of the first window held, what #5
allows) and `reestimated` (estimated again at each window) — and each arm is compared with equal
weight on the same days by the difference of daily Sharpe, its interval from a paired stationary
bootstrap; «beats» = the whole interval above 0 at `wf.confidence`, which has no default. The
sentence is one of three: a method beats equal fixed (a candidate for the owner), **only
re-estimated (the condition that reverses #5)**, or none (equal stays). The command changes no
knob: `config.load` refuses `weights.method` other than `equal`. Each run is a look at oos1 and
writes its ledger rows (§6).

### 5.5 Verdict — oos1, then oos2 once

`verdict/metrics.py` on the chosen portfolio's daily P&L (compendium §9.1): RAR%
(annualised slope of a regression of cumulative equity) and R-cubed, each recomputed on windows
shifted 0-3 months at each end, min and median kept; gain-to-pain; mean annual DD; time under water;
longest flat period; P(losing year); Sharpe on daily MTM. 🤔 RAR% on log equity needs a capital base;
until Q5 fixes the unit, compute it on cumulative P&L and say so.

`verdict/null.py` + `decide.py` — the decision (root `CLAUDE.md`: "an analysis ends in a decision"):
what the portfolio is compared against and what counts as passing is **Q11 = (d), decided
2026-10-04** — two readings, in this order, each a ledger row at step 27:

1. **`oos1`: the selected null** (`many.oos1`). 10,000 (`real.null_draws`) random admissible
   combinations **of the chosen portfolio's size K** — cliques of the same build graph, no search
   per draw (owner, 2026-10-05, R6; `search/random_k.py`) — each measured on `oos1` exactly as the
   chosen one. The figure is the **rank score**: the four metrics of §5.4, each one's worst over the
   shifted starts, mean signed rank inside {the draws + the chosen one}. Pass: above the draws' 95th
   percentile (`real.null_percentile`). **With fewer than 20 admissible combinations of size K the
   chosen one is ≥ 5 % of the draws and the bar is its own figure**: the verdict is «NO SE PUEDE
   JUZGAR», no percentile is printed and oos2 stays shut (K = 1 always ends here unless the pool has
   over 20 members). The random benchmark is read here and never on `build` (owner, 2026-09-29).
2. **`oos2`: the deflated Sharpe, once** (`oos2.read`). Only if 1 passed. The chosen portfolio's
   daily Sharpe on `oos2` minus the expected maximum of N trials (`ledger.trials.deflated`), N =
   **`ledger.trials.overall`, the whole project** (owner, 2026-10-05, R7), spread = the build
   Sharpes of the pool's study (`search/trials_real.py` stores them for this); pass: > 0.
   **One read, of one portfolio**: the pool's study is asked first whether a step-27 `oos2` row
   exists (same members → the stored reading, never recomputed; other members → refused), then
   `gate.allow(27, "oos2", symbol)` for every member's symbol, and the row is written whether it
   passes or not. 🔬 Executed only on synthetic pools and on a **pseudo** oos2 in the test root.

After that the segment is spent: what validates the combination from then on is live incubation
(M9). Whatever the reference,
the sentence carries the cost next to the gain, e.g. «la cartera de 6 (de 41 admisibles, 30.000
combinaciones probadas) gana a 6 al azar del mismo pool en el 92 % de las extracciones sobre
oos1; DD medio anual −4,1 % contra −6,3 %; deja fuera 35 estrategias». `DECISIONS.md` #12
(an "on probation" label) changes only the words available here.

**Did the diversification hold out of sample?** The pairwise measures of §5.2 (and effective N,
calm and stress) recomputed for the chosen members on the segments the verdict opened, every pair,
same thresholds. It
chooses nothing and removes nothing — the combination is fixed before it runs; a pair over threshold
out of sample is a part of the verdict block with its own state. This takes libros §5.9 «Clones»
(redundancy shows up in OOS daily P&L) without letting OOS choose the combination. Owner delegated
the call, 2026-09-30: choosing on OOS would turn the verdict into Katz's 625 % portfolio (libros §3.3
«bifurcaciones») — the OOS drawdown and co-loss the verdict reads are the very numbers an OOS filter
would have optimised. A pair over threshold here is reported and fails nothing (built so; the
owner's to change).

Also reported, not judged: the deflated Sharpe of the chosen portfolio with N from the ledger
(`ledger.trials.accumulated` + `deflated`), and the build→OOS retention of the objective.

### 5.6 The view

Inside the PORTFOLIOS zone (`ui/desktop/portfolios/`), a second tab «Construir»: pick a pool (and a
firm, when prohibition files exist), the drawer with every knob (`tooltips.py`), «Construir» enqueues
`python3 -m portfolio.common.construct.report …` on the daemon's `python` lane (`sqx/jobs.py`,
no SQX, no confirmation gate needed); the result is the contract dict painted by
`ui/desktop/blocks/` — tabs: Veredicto · Universo (reconciliation, coverage per segment) · Parejas
(grid of each measure, bars of failures per filter) · Búsqueda (funnel, score distribution of every
evaluated combination with the chosen one marked) · Cartera (equity build | oos1 | oos2 as `lines`
with the split marked, members table). New daemon router `ui/daemon/portfolios/api.py`, registered in
`ui/daemon/routers.py`. Terminal theme, `QFrame` named `term`. No new widget kind — if one seems
needed, ask (CONTRACT §2).

### 5.7 · `config.yaml` — every knob

Thresholds live in `ledger/thresholds.yaml` and appear here as `ledger:<key>` (the project's rule:
one source, `ledger.thresholds.fill`). "Owner" = decided; "AF" = AlphaForge's number, standing until
the owner changes it, shown as such in the drawer; "—" = blocked, no default, the run refuses to start.

| section.key | default | who |
|---|---|---|
| `pool.name` | — (argument) | the run |
| `pool.firm` · `pool.plan` | null (no prohibitions) | the run (`--firm`, `--plan`) |
| `funded.open_risk_cap` | — | **R5**, owner 2026-10-05 the rule; the fraction is open (§12, reading 5) |
| `stageb.shared_of` · `stageb.t1_gap` | `larger` · — | owner, 2026-10-05 · open |
| `equity.source` | — | **Q3** |
| `equity.clock` | — | **Q4** |
| `equity.reconcile_max_trades` | 3 | SQX's noise floor, `sqx/variants/curves.py:20` 🔬 |
| `pairs.pearson` · `.spearman` · `.co_loss` · `.tail` · `.rolling_whole` · `.rolling_recent` | `ledger:` 0.30 each | owner, 2026-09-29 |
| `pairs.tail_quantile` | 0.30 (worst 30 % of months) | owner (brief) / AF |
| `pairs.rolling_months` | 60 | owner (brief) / AF |
| `pairs.recent_span` | — | **Q9** |
| `pairs.frequency` | — | **Q7** |
| `pairs.sign` | — | **Q6** |
| `pairs.min_overlap_months` · `pairs.insufficient` | — | **Q8** |
| `pairs.stress_days` · `pairs.stress_quantile` · `pairs.stress_filter` | —, 0.05, — | **Q15**; 5 % from the compendium §4.2 |
| `pairs.relaxed` | {} | the run; any entry sets `relaxed: true` |
| `real.account` | 10,000 (with `funded.min_lot`, `funded.risk_grid`: the floor that sizes K) | **`DECISIONS.md` #2**, Council 2026-10-04 |
| `real.losing_year` · `real.rank_reference` | `calendar` · `seeds` | **Q10 = (a)**, Council 2026-10-04; the readings: owner, 2026-10-05 |
| `real.shift_months` · `real.shift_minimum` | 3 · `metric` | owner, 2026-10-05 (the shifted minimum; each metric's worst over the windows, ranked once — §12, reading 3) |
| `search.mode` | `ga` (`ga` · `admission` · `exhaustive`) | this plan |
| `search.exhaustive_max` | 1,000,000 combinations | owner, 2026-10-05 (was 100,000; ~11 min on one core at the limit) — above it the GA runs and its rank score still saturates (open, §12 reading 9) |
| `search.seeds` | 300 (= the population) | AF |
| `search.ga.{population, generations, elite, tournament, crossover, mutation, stagnation}` | 300, 100, 0.20, 4, 0.80, 0.40, 10 | AF |
| `real.increment` | `finite`; candidates enter in sequence | **Q16 = (c)**, provisional, Council 2026-10-04; the reading and the sequence: owner, 2026-10-05 |
| `weights.method` | `equal` | owner, 2026-09-29 (the only one); `weights/` since 2026-10-05 |
| `weights.unit` | — | **Q5** |
| `wf.lookback_years` · `wf.step_years` | 0 (everything before the window, so the first estimation is the whole `build`) · 3 | 🤔 this plan (AF: 6) · AF |
| `wf.confidence` · `wf.bootstrap_draws` | **null** — the command refuses · 2,000 | **open** · 🤔 this plan |
| `incubation.figure` · `incubation.history` · `incubation.band` | **null** · **null** · **null** — `register` refuses (`pnl`\|`sharpe` · the segments whose windows make the band · two percentiles) | **open** |
| `verdict.reference` · `verdict.pass` | oos1: 95th percentile of the selected null · oos2: deflated Sharpe > 0, one read | **Q11 = (d)**, Council 2026-10-04 |
| `verdict.shift_months` | 3 (windows shifted 0-3 months at each end) | compendium §9.1 |
| `real.null_draws` · `real.null_percentile` | 10,000 · 95 (`ledger:portfolio.verdict.*`): random admissible combinations of the chosen K, on oos1 | Council 2026-10-04; owner 2026-10-05 (R6) |
| `verdict.null_draws` | 100 whole searches — the funded F4 null, its own knob | 🤔 this plan |
| `verdict.pass_measure` · `verdict.pass_percentile` | `mc_p` · **null** (the funded bar on oos1; unset = «SIN CRITERIO (falta verdict.pass_percentile)») | owner 2026-10-05 · **open** |

No seed knob: every stochastic step draws fresh entropy and records the root it drew, as
`engines/nulls` does (owner, 2026-09-29, `knowhow/eng/nulls-seed-fresh-per-run.md`).

## 6 · Ledger rows

One run writes (Q12 decides the study id, and `symbol`/`timeframe` for a multi-asset row):

| row | step | segment | n_in | n_out | criterion | scores |
|---|---|---|---|---|---|---|
| the pairwise screen | 27 | build | pool after prohibitions | strategies with ≥ 1 admissible partner | `portfolio/pairs` + thresholds, `relaxed` in note | — (a screen, not a ranking) |
| the search | 27 | build | same | K (members chosen) | `portfolio/ga` or `portfolio/admission` | the build objective of **every** combination evaluated → `n_scored` = evaluations, `score_unit: per_period` |
| the verdict's look | 27 | oos1 | 1 | 1 or 0 | `portfolio/verdict/<null>` | — |
| the verdict's look | 27 | oos2 | 1 | 1 or 0 | same | — |

Step 27 because `docs/AgentPDFs/WORKFLOW.md` says the portfolio starts at 27 🔬; it is not in
`ledger.gate.STEPS`, which matters only under `ALGO_AUTONOMOUS=1` — and then the policy would refuse
oos2 to it until the owner adds a name to `reserved_for` (his file). Before opening any segment,
`gate.allow(27, segment, symbol)` for **every member's symbol**, as `look.admit` does. Every combination
evaluated is counted — including those of a run the owner discards and those of the admission mode.

## 7 · AlphaForge, file by file

Clone for reading only in the scratchpad; never read or use `TokenAlphaForge.txt`. "Port" means
rewrite into this project's style (functions, ≤ 500 lines, no classes, no dataclasses); nothing is
copied verbatim.

| AF file (lines) | verdict | why / what changes |
|---|---|---|
| `config.py` (97) | **rewrite as `config.yaml`** | the one-place idea stays; account, daily loss, DD, scaler knobs go (encargo 33's); thresholds → `ledger/thresholds.yaml` keys |
| `universe.py` (312) | **port and fix** | daily/monthly matrices and N×N precompute keep; `$0` fill → NaN outside history; `<6 → 0.0` → `insufficient`; realised-on-close-day → MTM (§5.1); same-asset matrix dropped |
| `generator/filters.py` (743) | **port and fix** | Pearson, Spearman, co-loss, tail, rolling kept; `abs()` pending Q6; stale "12-month" docstring (the code is 60); `<6 → pass` fixed; same-asset filter dropped; the matplotlib plot dropped |
| `generator/sampler.py` (143) | **port as is** (as a function) | exhaustive-or-proportional sampling for small spaces |
| `generator/genetic.py` (1037) | **rewrite** | keep greedy seeding, operators, stagnation on the absolute score, per-pair cache; drop the whole-history selection (leak), the min-max fitness, the soft DD check; split into `greedy.py` + `genetic.py` |
| `generator/parallel.py` (74) | **port as is** | SIGINT-safe process pool; 🤔 only if the GA needs processes at all (evaluation is µs) |
| `generator/pipeline.py` (448) | **rewrite** | its shape becomes `run.py`; the auto-rerun with offset seed goes (each rerun is a trial) |
| `generator/weighting.py` (324) | **ported** (`equal` at M4; risk parity, min-variance, HRP at M8, 2026-10-05) | HRP bug (§1) fixed; min-variance gets shrinkage; its silent `except → risk_parity` fallback goes |
| `generator/wf.py` (294) | **ported at M8, 2026-10-05** (`walkforward.py`, `wf.py`) | the weight walk-forward: the test a non-equal method must pass |
| `generator/fitness.py` (88) | **drop** | [AF✗] pool-relative 0.8/0.1/0.1; replaced by `objective.py` (Q10) |
| `generator/scaler.py` (129) | **drop** | sizing to the exact worst day: encargo 33's, and [AF✗] |
| `generator/validator.py` (131) | **drop** | DD on rescaled closed P&L: encargo 33's |
| `generator/combo_result.py` (77) | **drop** | a dataclass; results are dicts |
| `stress/mae_stress.py` (174) | **drop here** | [AF✗] (§7.4 of the compendium); encargo 33's stress |
| `analysis/correlation_deep.py` (301) | **rewrite later** | PCA / dendrogram math may feed "monoculture" (§4.6); its tail definition disagrees with the filter's; not in this plan's milestones |
| `portfolio.py` (54) | **drop** | its `correlation_matrix` correlates unaligned trades |
| `run_expandPortfolio.py` (338, repo root) | **rewrite** | → `admission.py` with a real marginal-contribution rule (§5.3) |
| `exporter.py`, `dashboard*.py` (677 + 2,009) | **drop** | interfaces live in `ui/`; `dashboard_mc.py`'s bootstrap belongs to encargo 33 if anywhere |

## 8 · Tests

Plain scripts in `tests/`, listed in its README (`CODESTYLE.md` § Tests). Synthetic data built so the
answer is known.

1. **`test_portfolio_measures.py`** — Pearson and Spearman equal scipy on random series; co-loss on a
   12-month hand table (answer 3/12); tail on a pair built to correlate only in its worst months;
   rolling: ρ = 0 for the first 60 months and ρ = 0.9 in the last 36 → whole max and recent max
   known; overlap: 5 shared months → `insufficient`, **never 0.0**; stress-day: independent on calm
   days, identical on the planted stress days → calm ≈ 0, stress = 1; effective N: k clones → 1,
   k independent → ≈ k.
2. **`test_portfolio_mtm.py`** — one long trade across three boundaries on hand-made M1 bars:
   floating at each boundary exact to the cent; close-day increment = realised − last floating;
   a same-day trade lands whole on its day; Σ daily = Σ `Profit/Loss` exactly; a weekend; an `EETUS`
   feed shifted −7 h; a DST-ambiguous hour counted, not guessed. Plus, on the archived USDJPY
   strategy (`AlgoData/archive/4d679e…`), rebuild vs SQX curve within the reconciliation tolerance —
   a golden check, skipped with a message when the archive is absent.
3. **`test_portfolio_search.py`** — a planted solution: 40 synthetic strategies of which exactly one
   6-set is a clique and scores best on build; greedy + GA must return it; exhaustive agrees on a
   small pool; admission adds a planted diversifier and refuses a planted clone (ρ = 0.95).
4. **`test_portfolio_segments.py`** — the segment discipline, two ways: (a) the search run on a
   matrix whose oos1/oos2 rows are `NaN` returns exactly what it returns on the full matrix, and a
   pool built so the oos-best combination differs from the build-best returns the build-best;
   (b) a source check: no module under `search/`, `pairs/`, `weights/` names `oos1`/`oos2`, and
   `run.py` passes them only the build slice. The test fails if either breaks.
5. **`test_portfolio_ledger.py`** — after a run on a temporary ledger, the search row's `n_scored`
   equals the rows of `search.parquet`, and there is one row per segment read.
6. **`test_portfolio_weights.py`** — every registry entry returns non-negative weights summing to 1
   over the given identities; `equal` returns 1/K.
7. **`test_portfolio_verdict.py`** — a pool of pure noise: the verdict must not pass more often than
   the null's nominal rate over 200 seeds (calibration); a planted edge must pass.

Each new analysis module gets a perf target in `perf/inputs/targets.py` (`CODESTYLE.md` §9): the
universe build, the pairs table, one search.

## 9 · Milestones

Each one ships alone, with its tests green, its manual chapter in `AlgoData/manual-fuentes/`
(Spanish, screenshots of real output; the family is **Q17**), `python3 tools/manual.py`, and ends
with `python3 tools/depmap.py && python3 tools/checks.py`. Chapter numbers are the next free ones
(77 onward today).

| # | ships | blocked by | chapter |
|---|---|---|---|
| **M0** | `core.paths.portfolio_dir`; `inputs/pool.py` (pool CSV, hash, prohibitions); `candidates.py` — lists archivable survivors of every step from the reports' `verdict.csv` files and prints, per candidate, the exact `python3 -m core.archive archive --project … --databank … --identity … --step … --family …` line; **runs none**; the development mark | Q2, Q13, Q14, `DECISIONS.md` #10 (near-survivors in or out); **the owner's go-ahead to archive** (the archive reads SQX install files and the daemon; `core/archive/README.md`) | 77-cartera-pool |
| **M1** | `inputs/source.py`, `equity/*`: SQX curve + rebuild + reconciliation + matrices, universe cache; tests 2 | Q1, Q3, Q4; M0 for more than one strategy (the rebuild and its tests run on the one archived strategy and synthetic data) | 78-cartera-universo |
| **M2** | `pairs/*`, `search/admissible.py`, relaxed flag, the Parejas tab data; tests 1 | Q6, Q7, Q8, Q9, Q15 | 78 (same chapter, section) |
| **M3** | `search/*`, ledger rows, `search.parquet`; tests 3, 4, 5 | — (all answered 2026-10-04; Q16 provisional) | 96-cartera-busqueda-por-rangos |
| **M4** | `weights/` with `equal`; test 6 | Q5 | 79 (section) |
| **M5** | `verdict/*`, `contract/*`, `many.py`, `report.py`, the hand-off package; test 7 | the open readings of Q11 (§12, 6-7); Q2 (oos2 must exist for the pool) | — |
| **M6** | the prohibition input end to end (hand-written file), `--firm` | encargo 33 for real files; nothing for the format | 80 (section) |
| **M7** | the «Construir» tab and `ui/daemon/portfolios/`; screenshots | M5 | `71-app-portfolios` extended |
| **M8** | more weight methods + AF `wf.py` walk-forward as the gate against equal | — (#5: never rebalance, 2026-10-04) | — |

**Status, 2026-10-05** (first built 2026-09-30, `portfolio/EXECUTION.md`; M3-M9, F3-F5 added 2026-10-05):

| # | status |
|---|---|
| M0 | ✅ code: `inputs/pool.py`, `inputs/source.py`, `candidates.py` (chapter 77). The pool itself: row «M0 pool» below |
| M1 | ✅ `equity/*` + `universe.py` (chapter 78): M1 rebuild licensed on the archived strategy (MAE 100 %, MFE 99.9 %, SQX's daily low 100 % of 3,983 days), EET daily matrix, firm-clock day tables and M5 blocks; parallel, 48 strategies in 15 s at 57 GB |
| M2 | ✅ `pairs/*`, `search/admissible.py`, the screen in `universe.py`: 500 strategies' 124,750 pairs in 30 s on 48 cores, graph in 1 s |
| F1 | ✅ `portfolio/funded/rules/`: 11 plans ≤ 10k, one-tick known answers, numba sweep = reference (2,500 × 2,500 in 3 ms) |
| F2 | ✅ engine (chapter 79): fixed-risk sizing from the step-24 stop, stage-A objective on 48 cores (~1,500-1,860 combinations/s, 1.3 GB), greedy + GA, ledger rows (pool study + each member's), the command. 🔬 2026-10-05 first run on `Test_nikkei_ref` (**test root, pair thresholds 0.90, cap passed with `--set`: not a result**): `hantec:express:10000:USD` 4,500 evaluations = 58 distinct of 103 admissible, best K = 3 at r 0.6 %, P(pass) 0.338, 13.5 s, 1.1 GB; `ftmo:2step:10000:USD` K = 3 at 0.8 %, P 0.166. The open-risk cap (R5) is built and required; the stop is read (`tests/test_portfolio_stopread.py`: the same combination with every stop ×2 goes from P 0.339 to 0.102 at 1 %). ⏳ the cap's fraction; a run on a real pool at 0.30 |
| M6 | ✅ 2026-10-05: prohibitions end to end with a hand-written TEST file (§2.1), `--firm`, members named; `tests/test_portfolio_pool.py`. The real folder holds the format only |
| F3 | ✅ engine (chapter 87); 🔬 2026-10-05 first real run on the stage-A run above (test root, not a result): 11 diverse finalists × 10 risks in 18.5 s, 1.8 GB; winner K = 4 at 0.6 %: D 0.317, T1 0.359, T2 0.302 (decides), 0.303 on fresh paths, against stage A's 0.328; Politis-White block 1-3 days. The three agree with stage A within 0.03 and T1 is optimistic on near-clones by construction (`knowhow/research/t1-optimistic-on-near-clones.md`). Perf target `portfolio.stage_b`: 4.0 s. ⏳ `stageb.t1_gap`; no verdict without oos2 |
| M0 pool | ✅ 2026-10-04: the 30 mothers of `Test_USDJPY_donchianUpperCrossUp_H1` carried to 16.5 are archived (`AlgoData/archive/`, step 16.5, from the files in the data root with `--sqx`: the project is on no install). None carries the step-24 stop; no pool is declared yet (§12, open reading 8) |
| M3 | ✅ 2026-10-04, code and known answers (`tests/test_portfolio_ranks.py`, chapter 96): `verdict/metrics.py`, `search/objective.py`, `exhaustive.py`, `choose.py`, `admission.py`, `trials_real.py`, the command `real.py`. The owner's readings of 2026-10-05 are in (R1, R2, R4, the shifted minimum, admission in sequence; `tests/test_portfolio_planted.py`, `_segments.py`, `_ledger.py`). 🔬 2026-10-05 first run on a declared pool with the step-24 stop — `Test_nikkei_ref`, **test root, pair thresholds relaxed to 0.90, not a result**: 103 admissible combinations, K = 1 chosen (ten near-clones). `real.shift_minimum: metric` set by the owner the same day. ⏳ a run on a real pool at 0.30 |
| M4 | ✅ 2026-10-05: `weights/` with `equal` as the one method (`REGISTRY`, `matrix`), read by `search/objective.py`; the Nikkei test run's `search.parquet` is byte-identical before and after the extraction; `tests/test_portfolio_weights.py`. The unit a weight multiplies is the fixed-risk P&L (§12, F2 unit of risk: «for funded and for everything») |
| M5 | ✅ 2026-10-05, built (chapter 101; `tests/test_portfolio_verdict_real.py`): `report.py`, `many.py`, `oos2.py`, `segment.py`, `handoff.py`, `contract/`, `verdict/deflate.py`, `decide_real.py`, `search/random_k.py`; thresholds `ledger:portfolio.verdict.null_draws` 10,000 and `.null_percentile` 95. Known answers: a planted trio beats the bar, a random trio of noise passes 5.0 % of 200 seeds, oos2 read once then stored / refused. 🔬 `Test_nikkei_ref`, **test root, relaxed, pseudo oos2, not a result**: K = 1 → «NO SE PUEDE JUZGAR» (10 admissible singles, the chosen one 9.8 % of the draws); a forced K = 3 → percentile 91.6 % of 37 trios, «NO PASA (oos1)»; 3.6-12 s. The real path's oos2 read has run on synthetic pools only. ⏳ the owner's readings in §12, 6-7; a pool with ≥ 20 admissible combinations of the chosen K |
| F4 | ✅ 2026-10-05, rebuilt on Q11 (d) (`funded_verdict.py`, chapter 87; `tests/test_portfolio_verdict.py`, `_verdict_funded.py`): oos1 alone on `mc_p`, then `oos2.read`. **The bar `verdict.pass_percentile` is unset**: the committed verdict is «SIN CRITERIO (falta verdict.pass_percentile)». 🔬 same test run as F3, 20 null searches (a test value; ~22 s per null search idle, 35-39 s busy, 2.0 GB): winner K = 2 at the 35th percentile on `mc_p` → SIN CRITERIO; with a TEST bar of 0.0 the pseudo oos2 was read once — Sharpe 0.0015 against 0.0273 expected from N = 383,600 (the test ledger), «NO PASA (oos2)» — and the next run, whose stage B chose another winner, was refused the segment. **Stage B's winner changed in each of three runs** (finalists within 0.003 of each other) |
| F5 | ✅ 2026-10-05, built (`funded/sim/`, `funded/decide/`, `deals.worth`; chapters 88, 102; `tests/test_funded_{sim,bank,price,decide}.py`). 🔬 the F4 test run's portfolio (K = 4, Hantec Express 10k), **test root, relaxed, test owner inputs, not a result**: 10,000 × 504 days, OOS edge 20 % of build's; 2,610 configurations in 86 s; the plan the portfolio was built for loses (EV at h = 50 % −71 ± 1 $ without re-buy, −176 with); the same paths on FTMO 2-Step and 1-Step 10k without re-buy give +10 to +14 ± 3-4 $ on two seeds, not eligible (another plan's portfolio); `none` beats `same_plan` on every plan; decision «ninguno». ⏳ the owner's inputs still `null` (`sim/README.md`), the horizon, and a funded verdict that passes — `verdict.pass_percentile` unset blocks any purchase |
| M8 | ✅ 2026-10-05, built (`weights/{risk_parity,min_variance,hrp}.py`, `walkforward.py`, `wf.py`; chapter 103; `tests/test_portfolio_weights.py`, `tests/test_portfolio_wf.py`). Known answers: 1/σ by hand, Ledoit-Wolf intensity, HRP invariant to column order, a planted volatility swap read «only re-estimated» by the three methods, noise read «none». 🔬 `Test_nikkei_ref`, **test root, relaxed 0.90, pseudo oos2, `wf.confidence=0.95` and `wf.step_years=1` as test values — a code test, not a finding**: forced K=3 and the 5-clique, 518 oos1 days in 2 windows, no arm beats equal (K=3 best: min-variance re-estimated +0.0029 [−0.0047, +0.0102] of daily Sharpe; K=5: every method below equal). `weights.method` stays `equal`; #5 not reversed. Not built: Carver handcrafting. Open: §12 readings 10-11 |
| M9 | **contract and reading built 2026-10-05; incubation is NOT running** (`incubation/`; chapter 104; `tests/test_portfolio_incubation.py`). Built: the frozen record of a judged portfolio, the row contract of its fresh days (the hand-off's `daily.parquet` columns, segment `incubation`, source `paper`\|`live`), the validator, the reading against the band of equal-length windows of its own history, one ledger row per reading. 🔬 on synthetic «live» rows only (test root). **Not built**: what produces the rows (the monthly SQX retest — a worker job with the owner's go-ahead — and the live-trade conversion), any stopping rule, the size ramp. 🔬 the band is not its nominal level: a [5, 95] band from ~10 independent windows flags a healthy portfolio 9.7 % of the time, and 12 monthly readings flag it at least once in 24 % (`knowhow/research/incubation-band-is-not-its-nominal-level.md`). Open: §12 reading 12 |
| M7 | ✅ 2026-10-05, built: `ui/daemon/portfolios/` (readers, `commands.plan` with the Spanish refusals and the oos2 confirmation, `bankjob`) and `ui/desktop/portfolios/` (board, module pages, calc, matrix, databank; the archive viewer stays as rail entry «Archivo»); `tests/test_ui_portfolios.py`. «Calcular» really ran on the test root (universe, real search, stage A, bank chain); the verdict (`report`) and `funded_b` buttons were exercised only up to preflight, dialog and nonce with the job stubbed. Not built: column-set chooser, checkboxes in «Carteras», segment shading; the null histogram lacks the p95 line |


**Verification level, 2026-10-05 — read before trusting any row above.** Every piece is built, has a
known-answer test, and ran on the **relaxed `Test_nikkei_ref` pool under the test root**
(`AlgoData/portfolio/_test/root`, pair thresholds 0.90, a pseudo oos2 cut from the tail, test values
for the null knobs). **No real result exists**: no real pool has been run, the real root holds no
portfolio run, ledger row or bank table, a real `oos2` has not been read, and incubation is not
running. Fixed since: `funded.open_risk_cap` 0.5 and `verdict.pass_percentile` 0.95 (2026-10-14), `wf.confidence` 0.95 joint
and `incubation.figure/history/band` (2026-10-15). `stageb.t1_gap` (close_to_open_blocks), `tax_rate` (informational) and `p_payout_denied` (0.05) were fixed on 2026-10-15. Knobs still `null` (the real run refuses), in `funded/sim/config.yaml`:
`owner.eurusd`, `payout_cushion`, `payout_fee`, `p_firm_closes_year`,
`gaps.hantec_endurance_payout_days`, `gaps.hantec_express_floor_after_payout`,
`gaps.ftmo_1step_floor_after_payout`. Unfixed findings: `OPEN.md` #104.

**The funded path (§14.5) runs F1-F5 after M0-M2 and before M3-M8** — the owner's priority is
funded accounts first (2026-09-30).

What the owner can run after each: M0 — the list of archive commands to approve; M1 — the
universe and its reconciliation for the pool; M2 — which pairs pass and why; M3 — a portfolio
chosen on build (no verdict yet: the result says so); M5 onward — the decision.

## 10 · Out of this plan, on purpose

The compendium items that are neither the engine's layers nor settled: label cards (§3.5),
monoculture/PCA (§4.6), joint stop-outs (§4.5), position overlap (§4.4 — AF's crude version dropped
by the owner), momentum/reversion mix (§4.7), haircut per family (§3.4), long/short split (§3.3),
every §6-§8 and §10-§11 item (encargo 33 or live). Each can enter later as a registry entry or a
verdict line, and each would be one more trial in the ledger.

## 11 · Risks and traps

- **No oos2 in the archive** (§1). On a pool without oos2 days the verdict can pass oos1 and then
  says «SIN VEREDICTO» for want of oos2 — it never calls an oos1 pass a verdict.
- **Mixed calendars** (§1 segments). An FX strategy is in oos1 in 2018-2019 while an index strategy
  is still in build: a naive calendar cut leaks one into the other (Q1).
- **Different feed clocks.** Infinox EET and the5ers Asia/Jerusalem change DST on different dates;
  a daily matrix built in each feed's own clock misaligns by an hour on those weeks (🤔 small for
  daily sums, but it moves co-loss on the boundary day).
- **Leg warm-up and duplicate dates** in SQX curves: slice by policy dates only.
- **Lot size is SQX's money management**: summing raw $ P&L weights each strategy by how SQX sized
  it (Q5). Correlations do not care; the objective, the verdict metrics and "equal weight" do.
- **Point value of JPY crosses** varies with the conversion rate: floating equity is approximate
  between boundaries, exact at the close (anchor). Reconciliation shows how much.
- **Swap between nights** is not in floating equity (§5.1 step 4).
- **The portfolio's intraday minimum is not the sum of members' daily minima.** The engine hands
  daily P&L; an intraday path is encargo 33's (from `trades.parquet` + M1).
- **Every rerun is a trial.** AF re-ran with an offset seed when a round found nothing; here each
  run, relaxed or not, is counted, and the window shows N.
- **Siblings will fail the filter** (owner expects it for parameter siblings, `portfolio/CLAUDE.md`);
  a pool of one mother's variants can yield no admissible pair — a valid answer, not a bug.
- **A cache is not a source**: `universe/<pool_hash>/` is keyed by pool hash **and** config hash;
  a threshold change rebuilds `pairs.parquet`, never reuses it.
- **HRP bug and `abs()`** in AF (§1) — do not port by copy.
- **The archive refuses while SQX runs the project** (`core/archive/README.md`); filling the pool is
  a window-and-conductor operation for the owner, not something the engine does.

## 12 · Questions for the owner

Not asked again: anything in `DECISIONS.md` «Settled by the owner» (engine first, sizing to 33, 0.30 thresholds,
no same-asset filter, pluggable weights with equal as baseline, build → oos1+oos2, same pool,
siblings face the filter, development pool from any step).

**Q1 · Segments when members are on different assets.** Each asset has its own build/oos1/oos2 dates.
(a) Each strategy contributes only its own segment's days; the search reads the days where **every**
member is in build (FX + index → 2013-09…2017), the verdict the days where every member is in
oos1/oos2 (→ 2020…2026); the rest is unused. (b) One portfolio-wide calendar (e.g. the latest build
end among members); strategies whose own segment differs contribute their other segment's days.
(c) A pool is only ever one segment calendar (FX+gold together, indices together).

**Q2 · Where oos2 comes from for the development pool.** (a) Only mothers that reached 16.5 enter:
their batch holds build+oos1+oos2, and `core/archive` learns to freeze the mother's full-history curve
(and its trades, which the batch does not hold — needs an orderstocsv on the conductor). (b) Any
archived survivor gets a retest over its whole window on a worker before entering (SQX, your
go-ahead each time). (c) Develop and test the engine with the verdict on oos1 only, labelled as such,
until the validated pool (step 26) arrives with oos2.

**Q3 · Which daily equity is authoritative.** SQX's curve is already mark-to-market. (a) SQX's curve;
the M1 rebuild only reconciles it and translates clocks (encargo 33). (b) The rebuild everywhere; SQX's
curve only checks it. (c) The rebuild where it reconciles within tolerance, SQX's curve otherwise, and
the result says which per strategy.

**Q4 · The clock of a "day" in the engine.** (a) Each feed's own broker clock, as SQX stamps it.
(b) UTC. (c) One reference broker clock for all (e.g. EET, the Infinox/most prop-firm server clock).

**Q5 · What "equal weight" weighs.** (a) Each strategy's P&L as SQX sized it (its money management,
100k account), w = 1/K. (b) Each strategy first scaled to equal risk on build (same daily volatility,
or same median |trade|), then 1/K. (c) P&L per lot (÷ `Size`), then 1/K.

**Q6 · Sign of the correlation thresholds.** (a) Reject ρ > 0.30 only (a negative correlation is a
hedge and passes). (b) Reject |ρ| > 0.30, as AlphaForge does. Co-loss is a frequency, unaffected.

**Q7 · Frequency of Pearson/Spearman.** (a) Monthly, as AlphaForge. (b) Daily. (c) Both, each at 0.30.

**Q8 · Pairs with too little overlap.** Minimum overlap: (a) 6 months (AF's number), (b) 24, (c) other.
And below it: (i) reject the pair, (ii) pass it with a flag that the result counts.

**Q9 · The "recent" rolling window.** On build, the recent stretch is: (a) the last 3 years of build
(AF: last 3 years of history), (b) the last 60-month window only, (c) other. Note: an index build is
~6 years, so a 60-month window gives ~16 windows there.

**Q10 · ANSWERED 2026-10-04: (a).** The search objective on build. (a) Equal-weight signed ranks of RAR%, R-cubed, gain-to-pain,
P(losing year) (compendium §2.7, §9.1). (b) One metric (daily MTM Sharpe, or RAR%/mean annual DD).
(c) 0/1 rules plus one metric to break ties.

**Q11 · ANSWERED 2026-10-04: (d) = (a) on oos1 + (c) on oos2.** What the verdict compares against, and what passes. (a) K random admissible combinations
from the same pool (a "monkey portfolio"): pass if the chosen one beats a set percentile of them on
oos1+oos2. (b) The equal-weighted whole pool: pass if the chosen portfolio beats it on the robust
metrics. (c) Absolute bars (e.g. deflated Sharpe > 0 with the ledger's N). (d) A combination. And the
percentile / bar is yours.

**Q12 · Ledger study for a portfolio.** (a) One study per pool, `PORTFOLIO_<pool>_construct`, with
`symbol` = the members' symbols joined and `timeframe` = `mixed`. (b) One row in **each member's**
study (every member's N grows by the look). (c) Both.

**Q13 · How a development strategy is marked.** (a) No new field: development = archived with
`step` < 26 (the mark is already there). (b) A `--development` flag on `core.archive archive` writing
`development: true` in `manifest.json`. (c) Only in the pool CSV (`development` column).

**Q14 · Which survivors form the development pool.** (a) Every archived-able survivor of every
project today (M0 lists them for you to approve). (b) One per mother (no variants). (c) Your list.
And `DECISIONS.md` #10: near-survivors in or out.

**Q15 · Stress days and effective N.** Stress days are: (a) the 5 % largest |daily move| of each
member's own asset, (b) of a risk proxy (USA500), (c) the pool's own worst 5 % days, (d) the named
crises (compendium §3.5). Effective N: (a) participation ratio of the correlation matrix's
eigenvalues, (b) K / (1 + (K−1)·mean ρ), (c) both reported. And is stress-day correlation a
**filter** at 0.30 or only reported?

**Q16 · ANSWERED 2026-10-04, provisional: (c).** Marginal contribution. A candidate enters when (a) its Euler increment to build Sharpe is
> 0, (b) the build objective of Q10 rises, (c) (a) plus the pairwise filters against every member.

**Q17 · Where the manual chapters go.** (a) Into `10-cierre` (the last family). (b) An eleventh PDF,
«Cartera». (c) Split: the view into `02-la-ventana`, the rest into (a) or (b).

**Q18 · ANSWERED 2026-09-30: the most pessimistic.** Which Monte Carlo decides for the funded path (§14.3b) when T1 (trade bootstrap per
strategy), T2 (synchronised trade blocks) and D (joint-daily blocks) disagree: (a) the most
pessimistic of the three; (b) T1 decides, T2 and D shown as warnings; (c) all three shown, the owner
decides case by case.

**Answered by the owner, 2026-09-30 (second session)** — each is now a rule, not a question:

| Q | answer |
|---|---|
| Q1 | **One portfolio-wide calendar, cut at the latest segment end among the members** (build ends at the latest build end, oos1 and oos2 likewise); a member contributes its own other segment's days inside the portfolio's segment, and the result counts them. USDJPY + XAUUSD share one calendar, so today nothing moves |
| Q2 | **Strategies of the recently run project that carry every segment, oos2 included**; if there are not enough, wait for that run to finish before testing on real data. 🔬 2026-09-30 11:20: `Test_USDJPY_donchianUpperCrossUp_H1` (15 mothers, on the custodian, at 16.5) — mothers have build+oos1 trades (`raw/…/CrossTF_Mothers`), full-history daily curves in 9 of 15 batches, **no oos2 trades yet**; `WFC_Build/OOS1/OOS2` hold 300 fabricated variants, none a mother. The engine is built and tested on synthetic data and the archived strategy meanwhile |
| Q3-Q5 | funded side settled by §14.4; real side still open |
| Q4 | shared universe: **one reference clock, EET** (NY-close server convention); the funded objective uses each firm's server day: FTMO `Europe/Prague` midnight (confirmed), **Hantec GMT+2 winter / GMT+3 summer, the standard MT5 NY-close clock = New York + 7 h — unconfirmed**, flagged in every result |
| Q6 | **reject \|ρ\| > 0.30** (AlphaForge's reading; strong negative correlation rejected too) |
| Q7 | **both monthly and daily**, each at 0.30; a pair must pass both |
| Q8 | **24 overlapping months; below it the pair is rejected** (`insufficient` → not admissible, never 0.0) |
| Q9 | **recent = the 60-month windows ending in the last 36 months of build** |
| Q12 | **both**: a study `PORTFOLIO_<pool>_construct` (symbols joined, timeframe `mixed`) **and** one row in each member's study |
| Q13 | **no new field: development = archived with `step` < 26**; the pool CSV's `development` column is filled from it, never by hand |
| Q14 | **every archivable survivor of every step**, `candidates.py` prints the commands and the owner approves; the owner archives (no go-ahead for the session to archive) |
| Q15 | stress days = **the worst 5 % of build days of the equal-weighted pool**; effective N **both formulas** (participation ratio and K/(1+(K−1)·mean ρ)), calm and stress; stress correlation **reported only, not a filter** |
| Q17 | **an eleventh manual PDF, «Cartera»** (chapters 77 onward) |
| `DECISIONS.md` #10 | **near-survivors enter, marked**; the result counts how many the portfolio chose |
| encargo 33 §6.1 | unconfirmed catalogue rules: **use the catalogue's reading, flagged «sin confirmar» in every result** |
| encargo 33 §6.2 | Friday close / no news: **the strategy is dropped from that plan's pool** (a trimmed strategy was never validated) |
| encargo 33 §6.3 | **one risk per phase** (1, 2, 3, funded), a searched dimension counted in the ledger; unchanged after a payout |
| rule machine (F1) | Hantec Express trailing max loss rises with the **intraday equity high** (floating included), locks at the starting balance at +6 % — unconfirmed, flagged; at daily resolution the day's high raises the floor **before** the day's low is checked (the conservative order). FTMO 1-step `eod_trailing` trails the **highest end-of-day balance** (closed) − 10 % of initial, capped at the initial — unconfirmed, flagged. A phase's target is met when the **closed balance at the day's end** ≥ target. «A day's profit» (profitable days, best-day and consistency rules) is the **closed P&L of the server day**; an FTMO trading day is a day with at least one position opened |
| Q8 (rolling) | a pair with 24-59 shared months is judged **without the rolling filters** (no full 60-month window), and the result counts such pairs (`n_without_rolling`) |
| tail sign | the tail filter is **one-sided** (reject only ρ > 0.30): two independent series read tail ≈ −0.46 by construction (`knowhow/research/pair-filters-false-rejection.md`) |
| F2 unit of risk | ~~a fixed lot, equal build volatility~~ — **superseded the same day by the owner: trade at FIXED RISK, for funded and for everything.** Each trade risks r % of the **initial** balance over a stop of **X·ATR(20), X = the step-24 p90** (one rule for all, fixed before looking, `ledger:portfolio.funded.stop_percentile`). The funded member is the strategy **with that stop grafted** — its step-24 SQX retest over build/oos1/oos2, not the stopless original. 🔬 SQX already sizes every trade at $1,000 over 4·ATR(20) (`ATRRiskBasedSizingFixedRisk`), so a member's P&L at risk r is SQX's × (r·balance/1,000) × (4/X) — a constant per strategy; the 0.01-lot minimum is checked trade by trade |
| F2 risk grid | **risk per trade 0.1 %…1.0 % of the initial balance, 10 levels**, every member at the same r (equal weight in R); the resulting daily volatility is reported |
| F2 horizon | a pass counts only **within 126 trading days (~6 months)** of the purchase; still open then = not passed; start days are the build days with a full horizon after them |
| F2 phases | stage A uses **one risk for every phase**; the ~50 finalists (stage B) sweep the risk per phase |
| pairs unit | unchanged: SQX's P&L is already fixed-risk, and a constant factor per strategy does not move a correlation |
| M0 survivors | **what the workflow carried forward is a candidate**: every mother with a 16.5 batch enters at step 16.5 whatever the earlier words said (the line shows them); `mcRetest` FAIL does not exclude; otherwise the word rules above |
| FTMO 1-step | **no minimum trading days** (FTMO FAQ, confirmed 2026-09-30; the best-day rule sets the practical floor of 2) |

**Decided by the Council on the owner's delegation, 2026-10-04** («Confío en el criterio de la
comunidad, hacedlo todo»; five members, confidence-weighted, threshold 2/3; options in
`docs/AgentPDFs/decisiones-pendientes-2026-10-04.md`). Each is a rule until the owner reverses it:

| Q | answer | what would reverse it |
|---|---|---|
| Q10 | **(a): equal-weight signed ranks of RAR %, R-cubed, gain-to-pain and P(losing year)**, on the equal-weighted combination, on `build` (`search/objective.py`, `verdict/metrics.py`) | a build→oos1 retention of the rank score no better than a single metric's on the first real pools (the ledger will show it); or Darwinex's own scoring once it is researched (§14.4) |
| Q11 | **(d)**: on `oos1` the chosen portfolio must beat the **95th percentile of 10,000 admissible random portfolios drawn by the same search**; on `oos2` its **deflated Sharpe with the ledger's N must be > 0**, read **once**, on the chosen portfolio only (§5.5) | a pool so small that the null redraws the chosen portfolio (the percentile then reads ~50 % whatever the edge); the owner moving the percentile |
| Q16 | **(c): Euler increment to the build Sharpe > 0 plus the pair filters against every member** — **provisional: unanimous option, low confidence** (`search/admission.py`) | the first pool where (b), the Q10 score rising, and (c) disagree on who enters and (b)'s choice holds better on `oos1`; any owner's word — it stays his call |
| `DECISIONS.md` #2 | **K and the per-symbol count are set by the funding economics**: the 10k account at the minimum lot, on the real side as on the funded one (§14.4) | an account where the minimum lot does not bind |
| `DECISIONS.md` #5 | **rebalancing: never** — fixed weights | a weight method that only beats equal weight when re-estimated (M8) |
| `DECISIONS.md` #12 | **no «unexplained, on probation» category** | the owner opening a separate sleeve |
| after `oos2` | **what validates the chosen combination once `oos2` is spent is live incubation** (M9, §14.5) — no new backtest segment is carved | — |
| M0 | **archive the development pool: yes** — done 2026-10-04 for the 30 mothers of `Test_USDJPY_donchianUpperCrossUp_H1` carried to 16.5 (Q2's pool), from files, no SQX command | — |

**Readings the Council's answers leave open** — built as a required knob with no default where the
code needed one (rule 11), otherwise not built; each is the owner's:

1. **Q10, ranks among what. DECIDED — owner, 2026-10-05: `real.rank_reference: seeds`.**
   Exhaustive search: the whole admissible space (no choice). GA: the greedy starting cliques,
   fixed before generation 0; ranking inside each generation is AlphaForge's flaw and is not offered.
2. **Q10, P(losing year). DECIDED — owner, 2026-10-05: `real.losing_year: calendar`** (share of
   calendar years of `build` that lose — ~10 values, many ties). `rolling` (every 252-day window)
   stays built behind the knob. A bootstrap reading (libros §5.6) is not built.
3. **Q10, the window. DECIDED — owner, 2026-10-05: the shifted minimum.** The search scores each
   combination on `build` with its **start** shifted 0, 1, 2 and 3 months (`real.shift_months: 3`,
   `search/objective.py::measure`) and keeps the minimum; the whole-window-once reading is gone.
   **The minimum of what — DECIDED, owner, 2026-10-05: `real.shift_minimum: metric`**: each metric
   takes its worst value over the four windows and the ranks are taken once (what §5.5 and the
   compendium §9.1 say of RAR % and R-cubed). The other reading (ranks inside each window, the
   lowest rank score kept) was not chosen and is no longer built.
4. **Q16, «Euler increment». DECIDED — owner, 2026-10-05: `real.increment: finite`** (Sharpe of
   the K+1 at equal weight minus the Sharpe of the K; `marginal` stays built behind the knob), **and
   several candidates enter IN SEQUENCE**: the best increment among the admissible enters, the base
   grows, the rest are re-judged — pair filters against every member of the new base, increment
   against the new base — until none is admissible with increment > 0 (`search/admission.py::sequence`;
   every judgement of every round is a ledger trial). Q16 (c) itself stays provisional.
5. **#2, the cap. RULE AND FRACTION DECIDED — owner, 2026-10-05 (R5), fraction 0.5 on 2026-10-14; readings confirmed 2026-10-15.** In the funded
   search the risk open at once is capped per plan: K × risk per trade ≤ `funded.open_risk_cap` ×
   the plan's maximum daily loss (`search/stagea.py::open_cap`, `capped`). No per-symbol cap.
   **Readings confirmed by the owner, 2026-10-15:** «the plan's maximum daily loss» is the catalogue's
   `daily_loss` as a fraction of the **initial** balance whatever the plan's daily basis (balance,
   or the higher of balance and equity); **in a trailing plan the room is the tighter of that and the
   trailing max loss** (the floor that breaks first; `stagea.room`); with one risk
   for every phase (stage A) the tightest challenge phase binds, with a risk per phase (stage B)
   each phase has its own. The real path (`real.py`) still has no cap: K × floor is printed.
6. **Q11, the oos1 figure. DECIDED — owner, 2026-10-05 (R6):** the **rank score** (the four
   signed ranks of the search, taken among the 10,000 draws plus the chosen one), and the null is
   **random admissible combinations of the same size K**, no search per draw. Readings confirmed by the
   owner, 2026-10-15: «same size» is the chosen portfolio's K; each metric is its worst over the
   shifted starts on oos1, as on build; under 20 admissible combinations of that K the answer is
   «no se puede juzgar», neither pass nor fail.
7. **Q11, the ledger's N on oos2. DECIDED — owner, 2026-10-05 (R7): `ledger.trials.overall`**, the
   whole project. 🤔 Readings the code took: «deflated Sharpe > 0» is the Sharpe minus the expected
   maximum of N trials (DSR > 0.5), not DSR > 0.95; the spread is the pool's own build Sharpes, so a
   pool searched by the funded path alone cannot be deflated and its oos2 stays shut; the read is
   one **per pool** — the real path and every funded plan of one pool share it; `overall` counts a
   portfolio search once in the pool's study and once more in each member's (Q12 b), so N is
   inflated by the portfolio rows.
8. **M0, the pool's extent.** `candidates.py` lists 182,464 archive commands today, 182,220 of them
   step-8 survivors of the `Test_Calib_*` calibration populations (and 182,045 with an empty
   `--family`). Archived: Q2's reading only. **Decided — owner, 2026-10-15 (F6, A):** the development pool excludes
   `Test_Calib_*` and everything built with costs before 2026-10-01; only current-cost work enters
   (enforced in `candidates.in_pool`, `tests/test_portfolio_candidates_pool.py`).
9. **Q10/R1, the GA's reference saturates** (found 2026-10-05, 🔬 on the planted pool of
   `tests/portfolio_planted.py` forced to the GA). `seeds` are greedy MAXIMAL cliques; a combination
   that beats every seed on the four metrics scores 1.0, every better one scores 1.0 too, and the GA
   stops on stagnation without ever trying the small K where the best portfolio was ({A, B}; it
   returned {A, B, N0, N1, N3}). The exhaustive search is not affected and is what runs up to
   `real.exhaustive_max` = 1,000,000 combinations (raised from 100,000 by the owner, 2026-10-05:
   ~11 min on one core at the limit; 100,000 took ~70 s with the four windows). Above the limit the
   GA still runs and its rank score still saturates; ranking the GA in another fixed set (random
   cliques of every size): owner, 2026-10-15 (F7f) — leave as is until a real pool exceeds the limit.
10. **M8, what «beats equal weight» means** (built 2026-10-05). `wf.confidence` = 0.95
   (owner, 2026-10-15, F4 B): JOINT, Bonferroni over the arms compared (≈0.99 per arm; `walkforward.compare`).
   Built on this plan's reading, each the owner's to move:
   the figure is the difference of daily Sharpe (not the Q10 rank score); the test is oos1 alone, so every run is one more look at it; `wf.lookback_years`
   0 (expanding) against AF's rolling 6; the reversal condition of #5 is read literally — the
   re-estimated arm beats equal and the fixed arm does not.
11. **M8, which methods.** Risk parity, minimum variance and HRP are built; Carver handcrafting
   is not (its correlation groups and its diversification multiplier need thresholds nobody set).
12. **M9, everything the plan does not fix.** `incubation.figure`, `.history` and `.band` are
   `pnl`, `[build, oos1, oos2]`, `[5, 100]` (owner, 2026-10-15, F5). Not decided and not built: how many flagged readings retire a portfolio or a member, how
   long incubation lasts, the correction for reading every month, the size ramp, whether a
   portfolio whose verdict failed may be registered (today it may; the verdict is written in the
   record), and whether each reading takes the whole fresh stretch since registration (built) or
   only the last month.

Encargo 33 §6.4 (re-buy: both policies, compared) and the haircuts of §6.7 (0-100 % in quarters, 50 % decides) were
answered by the owner on 2026-10-05 (`funded/sim/config.yaml`). Still open besides those: the unseen data of §6.7
(`DECISIONS.md` #11) and what encargo 33 §6 lists under «Lo que la primera corrida real dejó abierto».

Open decisions and where they block: `DECISIONS.md` #6 → encargo 33, feeds M6's file. (#2, #5, #12
decided 2026-10-04; #10 on 2026-09-30.)

## 13 · What the two dossiers say about each question

Read 2026-09-30 from `docs/AgentPDFs/ideas-de-internet-y-libros-2026-09-27.md` («libros», with its
section) and `docs/AgentPDFs/ideas-de-edge-2026-09-26.md` («edge», with its idea letter; its ideas are
**accepted by the owner, 2026-09-26**, the libros entries are candidates). This is evidence for the
owner's answer, not the answer: nothing below is a default. "Silent" = neither dossier addresses it.

| Q | what the dossiers say | where |
|---|---|---|
| Q1 segments across assets | Silent on mixed calendars. The nearest principle: selection of universe or thresholds on data that includes the test stretch is a leak (Fitschen's pairs chosen by whole-history ρ lost their edge when redone) | libros §3.7 «Fugas en la elección del universo» |
| Q2 oos2 | OOS is spent once (Aronson, Katsanos); **new bars after the last segment are the only renewable, unselected OOS** — every past survivor meets them unseen | libros §3.5; edge A |
| Q3 equity source | Daily **mark-to-market**, never closed trades (Trout; closed-trade equity hides open drawdowns); a second engine reconciling the first trade by trade is how cost bugs are caught | libros §3.8 «Unidades correctas», §3.7 «Un segundo motor» |
| Q4 clock | Broker servers run GMT+2/+3 with New York close, London and New York change DST weeks apart, D1 boundaries differ from Dukascopy's; test the edge at the broker's own boundaries | libros §5.3 «Horario de verano y hora del servidor» |
| Q5 unit of equal weight | **Edge E (accepted): measure in risk units — R per trade or a volatility size frozen before looking — not dollars**; a fixed lot on gold overweights recent years. Carver: equal weight **or equal risk**, vol-parity inside groups. Tharp: the sizing base matters more than the %; without a stop, ATR volatility is the only coherent base. Trap: R needs a frozen definition or it is a free parameter | edge E; libros §5.9 «Pesos iguales», §5.7 «Riesgo por volatilidad…», §3.8 «Qué es 1R» |
| Q6 sign | Silent on the sign itself. Every example of a diversifier is a low or opposite bet: Galante's short fund 1:1 with the Nasdaq halved its drawdowns; Hite keeps weak systems for low correlation; Covel counts 2×2 monthly signs rather than ρ | libros §5.9 «Contribución marginal», «Diversificar…» |
| Q7 frequency | For risk, daily: the daily cap breaks on same-day co-losses, drawdown on daily equity not month end (Faith: MAR 1.22 → 0.99), Sharpe on daily MTM (Trout). Katsanos: Spearman on changes, look at the scatter, one outlier moves r | libros §3.8, §5.9 «días de estrés», §4.8 «Correlación móvil inestable» |
| Q8 minimum overlap | Silent on a number. 🤔 Arithmetic, not a source: the standard error of ρ is ≈ 1/√n, so telling ρ = 0.30 from 0 at 2σ needs ≈ 44 observations; with 6 months the 0.30 threshold cannot discriminate | — |
| Q9 recent window | Katsanos: correlation between markets swings by regime (S&P–Nikkei yearly r from −0.22 to 0.84); «look at the rate of change of the correlation before trading it». No window length given | libros §4.8 |
| Q10 search objective | Combine metrics by **equal-weight signed ranks or 0/1** (Chan, Eckhardt, Kahneman). The fitness is an experimental variable (Katz: net profit picks crash-only systems; Fitschen: gain-to-pain). **Smoothness selects fragility** — Sharpe/R² alone lean to negative skew (Faith, Harding). Growth is m − s²/2 (Chan) | libros §3.8 (four entries), §1.10 |
| Q11 verdict reference | **The null must pass through the same selection** (Aronson, Katz: the best of N random sets, chosen the same way, is the null — not one random set). Judge OOS against the **band of equal-length in-sample windows**, not zero (Fitschen, Seidler). Window-robust metrics (RAR%, R³, shifted windows). Apply the project's own build→OOS haircut (ledger; external 0.4–0.75). The IS→OOS drop is first regression to the mean. Equal weight is the reference any optimisation must beat | libros §3.1 «Monos seleccionados», §3.5, §3.8, §5.6 «El descuento propio», §3.10, §5.9 |
| Q12 ledger study | **Edge 9 (accepted): multiplicity between studies** — a survivor's DSR against the whole factory's N. Every fork, overlay, exclusion after looking and «universe chosen from a matrix already seen» is a trial (Katz's 625 % OOS portfolio) | edge 9; libros §3.3 «bifurcaciones», §6.1, §6.2 |
| Q13 development mark | Silent | — |
| Q14 development pool | **Keep near-survivors** for portfolio and confluence (Shaw, Hite, Galante; top-30 #29) — `DECISIONS.md` #10. Declare the universe before looking. ⚠ Tension: **edge B (accepted) trades the plateau** (equal-weighted stable variants), libros §5.9 «Clones» says plateau neighbours are the Turtles' S1+S2 error (−80 % real vs −50 % believed); the owner already settled that siblings face the filter | libros §1.14, §5.9, §6.1; edge B |
| Q15 stress and effective N | Stress days: the 5 % largest \|move\| of the asset **or** a risk proxy, the named crises, **and** the survivors' own worst days; report effective N **in calm and in stress**; «ρ 0.1 overall and 0.8 in stress is one strategy for risk» (LTCM, BIS Aug 2024; value 5, top-30 #14). No formula for effective N; Aronson warns N_eff from correlation clusters is too small — calibrate by simulation | libros §5.9, §3.3 «Calibrar el N efectivo» |
| Q16 marginal contribution | Admit only if the **incremental Sharpe to the existing book is positive net of cost** (Euler decomposition, arXiv 1807.09864); pre-register the expected increment and report the realised one; judge long and short sides separately **and** together before cutting one (Faith: R³ 1.19 and 0.41 → 5.20 together) | libros §5.9 «Contribución marginal» |
| Q17 manual | Silent | — |

**Resolved, 2026-09-30:** libros §5.9 «Clones» proposes the redundancy filter on **OOS** daily P&L
— written for the gate's filter over single strategies. Here the combination is still chosen on
`build` only; the OOS correlation enters as the verdict's check «did the diversification hold» (§5.5).

**Candidates for the verdict and the view, each the owner's to accept** (all from libros, none in the
milestones yet): crisis-coverage label per segment (§5.5, top-30 #23); P&L in the market's extreme
months (§5.5); 2×2 table of monthly signs (§5.9, §6.6); P(profit) over rolling windows against the
monkey (§3.8, §5.6); start-date distributions (§5.6); serious-losses sheet (§5.6); P(losing year)
(§5.6); robust twin of every headline figure (§3.8); monoculture / factor exposure of the book (§5.9);
momentum-vs-reversion and convexity label per member (§5.9, §5.5, top-30 #16); persistence or
reversion of strategy results before any rotation (§5.9, top-30 #24).

## 14 · The funded path — settled 2026-09-30

`DECISIONS.md` #13, answered by the session: the owner delegated it («lo dejo en tus manos… dame lo
que consideres mejor»), stating his priorities: **funded accounts first and hard**, real trading at
Darwinex and DarwinIA afterwards. **The funded portfolio is chosen by the funded yardstick inside the
engine, on `build`, and judged on `oos1`+`oos2`**; encargo 33 keeps the economics and stops searching
portfolios. One search, one ledger count.

### 14.1 Why

A funded account is an option: the loss is capped at the fee, the gain comes only if the path reaches
the target before a rule breaks. The rules read the **floating** equity — the owner's point, and the
catalogue confirms it (`AlgoData/funding/funding.sqlite`, table `rules`, read 2026-09-30):

| rule | reads | status |
|---|---|---|
| FTMO daily loss | closed + floating during the CE(S)T day vs balance at midnight − X % of initial | confirmed |
| Hantec daily loss | a % of **max(balance, equity) at the previous 00:00 server time**, breached on equity | unconfirmed |
| Hantec Express max loss | 6 % trailing, locks at the starting balance once +6 % is reached | confirmed |
| Hantec Instant / Instant24 max loss | trails the **closed-balance** high-water mark | confirmed |

So the **MAE side** (worst floating inside the day) is what breaks daily-loss and max-loss rules, and
the **MFE side** matters too wherever the reference is an equity high: under Hantec's daily basis, a
large floating profit at 00:00 raises the next day's base, and giving it back counts as loss (libros
§5.8 «Beneficio abierto devuelto»). Two combinations with the same Sharpe differ exactly in these
tails; choosing by a real-account yardstick and sizing afterwards cannot see it. And encargo 33 §3.4
listed «cartera» among its own variables on every segment — a second, uncounted-against-the-engine
portfolio search on the data the verdict needs.

### 14.2 Floating equity in the universe (extends §5.1)

Per member, per **server day of the firm** (its clock, its midnight — the daily loss resets there):
`close` (MTM at the boundary, §5.1), `low` (worst floating equity inside the day) and `high` (best).
From M1: a long position's worst price in a minute is its `Low`, a short's is its `High`; closed P&L of
the day is added at its close minute. `low`/`high` of a member are exact; of a **combination** they
are not the sum of the members' (the worst minutes do not coincide):

- **bound**: Σ members' daily `low` — free, but 🔬 **it overstates the worst intraday loss by ×1.57
  (median) and ×2.89 (p95)** on a 10-member test, and it penalises exactly the diversified
  combinations the search is looking for (their worst minutes do not coincide). Not used to rank;
- **M5 joint**, for the search (stage A): each member's worst floating per 5-minute block (float32,
  ~7 MB per member for `low`, the same for `high`), summed per combination, min per server day —
  🔬 equal to the exact M1 figure on that test (median and p95 ×1.000, same worst day), 20 ms per
  10-member combination;
- **exact M1**, for the shortlist (stage B) and the verdict: the minute path summed on one grid,
  224 ms per 10-member combination.
  → `knowhow/perf/intraday-floating-resolution.md`.

**Known-answer check that licenses the rebuild:** per trade, the rebuilt worst and best floating over
its life must match SQX's own `MAE ($)` and `MFE ($)` (account currency, `knowhow/export/orderstocsv-schema.md`)
within a tolerance, on the archived strategy and on every pool member (`reconcile.py`). 🔬 Measured
2026-09-30 (`knowhow/export/mae-mfe-from-m1.md`): SQX takes the **M1 wicks** from the entry minute to the
minute **before** the exit, against the fill price — MAE exact to 1 $ on 2,094 of 2,094 trades, MFE on
99.9 %; minute closes miss by a median 20 $. The rebuild uses that window and those prices.

**The export gives the size of each excursion, never its moment** (owner, 2026-09-30). `MAE ($)` and
`MFE ($)` are one number per trade; a daily rule needs *when*. That is what the M1 rebuild supplies:
the minute of every extreme, per position, so the columns are only the check above, never the source.
What stays unknown, and how each is handled:

- **Inside one minute** the order of high and low is unknown. Each position takes its own worst price
  of the minute at once — conservative by at most one minute's range.
- **Shorts** (owner, 2026-09-30): the same wicks — a short's worst is the minute's `High`. The first
  short strategy's reconciliation against `MAE ($)` confirms it.
- **No M1 for the index CFDs** 🔬 (DAX40, DJ30, NIKKEI225, USA500, USATEC): the owner imports them
  when needed (2026-09-30). **Development uses USDJPY and XAUUSD.**
- **Without bars** (a feed not in `AlgoData/bars/`): only the MAE bound — every trade's MAE assumed to
  land on the same server day as the other open positions' — and the result says so, as encargo 33
  §3.2 already requires.
- **A second known answer, strategy level:** SQX's `MaxIntradayDrawdown` and `MaxTSIntradayDrawdown`
  exist in a variant batch's `segments.parquet` (16.5 mothers, per segment) though not in the
  archive's `harvest/metrics.parquet` 🔬 — the rebuilt intraday drawdown of the mother must match them.

### 14.3 The compute funnel — coarse to fine, each stage counted

The two-level Monte Carlo (the account's path inside a plan; the bank's cash across purchases) is only
affordable if the expensive levels see few candidates. Estimates 🤔, numba, one core; the machine
gives the `python` lane many.

| stage | who | on what | how | per candidate | candidates |
|---|---|---|---|---|---|
| **A · search** | engine `objective.py` `funded` | every combination the GA evaluates, one plan | the plan's rule machine run from **every start day of `build`** on the real path (start-date distribution, libros §5.6, compendium §7.2 — no resampling), on unit-risk daily `close` and the **M5 joint** `low`/`high`, over a grid of ~10 risk levels → best empirical P(pass) | M5 joint 20 ms 🔬 + rules ~2.5 M steps ≈ 2-5 ms 🤔 | ~30,000 per plan → ~12 min on one core, ~1 min on 12 |
| **B · shortlist** | engine | top ~50 **diverse** combinations of stage A per plan (no two sharing more than half their members) | **exact** intraday `low`/`high` from M1; rule machine on **joint-daily block bootstrap** (~20 days) **and** trade bootstrap (owner: MC of every kind, `portfolio/CLAUDE.md`), 10,000 paths × risk grid → P(pass) per phase, time to pass, which rule fails | ~10,000 × 250 × 10 ≈ 25 M steps ≈ 50-100 ms | 50 per plan → seconds |
| **verdict** | engine `verdict/` | stage B's winner per plan | the same measures on `oos1` alone, against the selected null (the same search run on random admissible combinations), then the deflated Sharpe on `oos2` once (Q11 d), plus «did the diversification hold» | — | 1 per plan |
| **C · bank** | encargo 33 `funded/sim/` | the verdict's winner per plan, and the monkey | **one long bootstrapped path per draw; accounts are bought one after another on it** — each new account starts the day the previous failed or paid out, so consecutive accounts share the regime and fail together as they would (encargo 33 §1.3); fees, rebuys, phases, payouts every N days, add-ons, haircut `h`, the 1,000 € budget; outputs the bank's EV, its drawdown, P(first payout) | ~10,000 draws × ~1,250 days ≈ 12 M steps ≈ 30-60 ms per (plan, add-on set, risk per phase) | ~9 plans × add-on sets × risk grid → minutes |

Why stage A uses the real path and not a Monte Carlo: it must rank 30,000 candidates on one segment
without randomness moving the ranking; start dates give ~2,500 honest, correlated trials of «buy the
challenge that day». Why stage C walks one long path instead of nesting two Monte Carlos: a nested
«simulate an account inside each bank draw» multiplies the costs; sequential accounts on one path cost
the same as one account path per draw and keep the correlation between consecutive attempts, which a
table of independent attempt outcomes would lose.

**Is minute resolution affordable here?** 🔬 Measured 2026-09-30 on one core: one strategy's minute
path over 8.7 M bars costs 0.08 s, the day's worst 0.16 s, reading the feed's M1 0.55 s (once per feed),
peak 1.2 GB. The design keeps minutes out of every loop that repeats:

- the universe stores per member only the daily `close`/`low`/`high` (500 strategies × 6,200 days × 3
  ≈ 75 MB), built once in ~2-3 min on one core for 500 strategies; minute paths are never stored
  (they would be ~70 MB each, 35 GB for 500);
- stage A sums per-member **M5** arrays (500 members × 2 × 7 MB ≈ 7 GB; 50 development members
  ≈ 0.7 GB), 20 ms per combination;
- stage B rebuilds the **M1** minutes only for the shortlist: 224 ms per 10-member combination 🔬,
  50 per plan ≈ 12 s on one core;
- **no Monte Carlo runs at the minute level**: the block bootstrap resamples whole days, each carrying
  its exact intraday `low`/`high`, so 10,000 paths cost what daily paths cost. A risk level scales them
  linearly (weights fixed), so the risk grid does not rebuild anything.

The binding constraint is RAM, not CPU: ~1.2 GB per worker against the 20 GB Python reserve → ~12
parallel workers, not 96 (`knowhow/perf/ram-budget.md`).

**Ledger:** stage A writes the search row (`n_scored` = combinations × plans); stage B one row per plan
(candidates = shortlist × risk levels); the verdict one row per segment read; stage C its own rows
(encargo 33 §3.4) for plans × add-ons × risk. The risk grid is a searched dimension and counts.

### 14.3b Monte Carlo at the trade level, with the floating inside each trade

Owner, 2026-09-29 (`portfolio/CLAUDE.md`): Monte Carlo of every kind, **the trade bootstrap
included**; he restated on 2026-09-30 that resampling should be at trade level. The unit of the
trade-level flavours is **a whole trade carrying its own floating path**: per trade, its worst and
best floating per 5-minute block since entry (M5, §14.2) and its final P&L, at unit risk. A resampled
trade therefore brings its real MAE, MFE and their timing inside the trade; nothing is cut mid-trade.

| flavour | what is drawn | keeps | loses |
|---|---|---|---|
| **T1 · trade bootstrap per strategy** | each member's trades with replacement from its own pool, laid end to end with gaps drawn from its own history; members drawn independently | order luck and composition luck of each strategy; every trade's intraday path | co-movement: members' bad trades stop coinciding — the portfolio drawdown reads too small (libros §5.9, Faith pp. 199-205, Fitschen pp. 161-165) |
| **T2 · synchronised trade blocks** 🤔 (this plan's proposal) | a calendar window (~20 trading days); **all members' trades that opened in it**, together, each whole | co-movement across members **and** whole trades with their floating | fewer distinct blocks than trades (less variety) |
| **D · joint-daily block bootstrap** | ~20-day blocks of the joint daily matrix (`close`, `low`, `high`) | co-movement; cheapest | cuts open trades at block edges |

All three run in stage B and in the funded verdict; each result is shown. **The most pessimistic of
the three decides** (owner, 2026-09-30, Q18); T1 and T2 accepted by him the same day.

**Block length (T2, D) is measured, not chosen** (owner asked whether 20 days is right when an
account can die in one week): the block length only sets how long a run of dependent days survives
the resampling — the rules are still checked every day, so a one-week blow-up inside a block is
kept whole. **Shorter blocks break clusters of losses apart and read the risk as smaller**; longer
ones repeat history with less variety. So: stationary bootstrap (geometric random lengths), mean
length by Politis-White on the combination's daily P&L (`engines.inference.snooping.superior.block_length`),
**plus** a sweep (5, 10, 20, 40 trading days, as `portfolio/common/monteCarlo/inputs/config.block_sizes`
does for trades), and the most pessimistic length decides — the same rule as Q18. The trade-level machinery exists for single streams in
`portfolio/common/monteCarlo/` (`inputs/stream.portfolio()` concatenates members' trades; its families
A and B are order and composition luck) — it reads closed P&L only; the floating path per trade is the
extension, and `simulate/stability.py`'s check (are the draws enough?) is reused.

Cost 🤔 (from the measured 0.022 s to lay one member's 2,094 trades over 14 years at M1): a path is a
**challenge horizon** (~6 months), not 14 years, so ~10 ms per 10-member path at M5 → 10,000 paths
≈ 100 s per combination → the 50 finalists of a plan ≈ 80 min on one core, ~7 min on 12. Stage C
(years-long bank paths over plans × add-ons × risk) is heavier: there the sweep runs on D and the
top configurations are re-run on T1/T2. A perf target measures it before F3 ships —
🔬 `portfolio.stage_b`, 2026-10-05: one 5-member combination, 11 path sets × 10,000 paths × 100
risk settings, 4.0 s wall (46 s CPU), 670 MB.

### 14.4 What moves

- **Encargo 33 keeps:** the catalogue, the firm's prohibitions (pool filter before the search), the
  rule functions (`portfolio/funded/rules/`, pure, known-answer tests — its deliverable 2), the bank
  simulation (stage C), the monkey per plan, add-ons as ΔEV − price, the haircut `h`, the decision
  sentence and its view. **It no longer chooses the portfolio.**
- **The engine gains:** `--firm F --plan P`, the `funded` objective (stage A), the shortlist and stage B
  in `search/`, calling `portfolio.funded.rules` — the engine imports the rules, it does not own them.
- **`DECISIONS.md` #2 (K) on the funded side:** on a 10k account, the risk of each member at the
  minimum lot (0.01) caps K; the search runs K from 1 to the largest feasible for that plan.
- **Q3, Q4, Q5 on the funded side stop being choices:** M1 rebuild on the firm's server day, in unit
  risk (edge E). They stay open for the real account.
- **The real account** keeps the plan's §1-§12 path. Because the owner will trade real money at
  Darwinex and DarwinIA, its yardstick (Q10) should later mirror how Darwinex scores and risk-normalises
  a strategy — 🤔 not researched here (published rules: `knowhow/research/darwinex-darwinia-published-rules.md`); a question for when the funded path works.

### 14.5 Order

The engine still comes first; encargo 33's rule functions move up because stage A needs them.

| # | ships | blocked by |
|---|---|---|
| M0-M2 | as §9, shared, plus §14.2 (server-day `close`/`low`/`high`, MAE/MFE reconciliation) in M1 | as §9 |
| **F1** | encargo 33 deliverable 2: the rule machine as pure functions, FTMO and Hantec ≤ 10k USD plans, known-answer paths that break each rule by one tick | 33 §6 questions 1-3 (catalogue gaps, Friday close / news, risk per phase) |
| **F2** | stage A: `objective.py` `funded`, K up to the lot-feasible maximum | F1, M2 |
| **F3** | stage B: exact joint intraday, both bootstraps, shortlist | F2 |
| **F4** | funded verdict: `oos1` against the selected null, then `oos2` once (M5 with the funded yardstick; `funded_verdict.py`) | F3, Q11; the bar `verdict.pass_percentile` is the owner's, unset |
| **F5** | encargo 33 stage C: the bank simulation, the monkey, add-ons, `h`, the table of 33 §4 | F4 |
| M3-M8 | the real-account path | as §9 |
| **M9** | **what validates the combination once `oos2` is spent — live incubation (Council, 2026-10-04).** Edge A for the chosen portfolio: each month, the members retested in SQX on the bars after `oos2` (a worker job — the owner's go-ahead each time) and the portfolio's paper-OOS row in the ledger, read against the band of equal-length windows of its own history (libros §3.5). **One retest, two readers**: the same fresh-stretch retest feeds the planned `weeklyReconciler` (`OPEN.md` #78 — live trades vs the SQX backtest of the same days), and the §14.2 rebuild applied to the live trades on the broker's M1 gives live floating vs backtest floating — the reconciliation of MAE, not only of P&L. **2026-10-05: the record, the row contract and the reading are built (`incubation/`); nothing produces rows yet — incubation is not running** | a chosen portfolio; the owner's go-ahead |
