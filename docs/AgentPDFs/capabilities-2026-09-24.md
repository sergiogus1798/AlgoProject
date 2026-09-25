# AlgoProject — Capabilities, and Everything Already Built

**What this is.** A briefing for a reasoning agent that is helping design new robustness tests for
this project but has only seen fragments of it. It answers three questions: **what this toolchain
can actually do**, **what is already implemented** (so nothing is proposed twice), and **what is
hard-blocked** (so nothing is proposed that cannot be built).

Written 2026-09-24 from the source tree, not from memory. Every empirical number carries the
strategy, databank or feed it was measured on. In English on purpose — its reader is an agent, not
the project's owner, whose own documents are in Spanish.

**How to use it.** Sections 1–3 are the machine and the pipeline. Section 4 is the inventory of what
exists — skim the *question* column, not the file names. Section 5 is what is designed but
unbuilt. **Sections 6 and 7 are the ones to read before proposing anything**: they are the
constraints and the measured facts that kill most obvious ideas. Section 8 is an honest list of
what nobody has covered.

---

## 1. The machine

### 1.1 Topology

StrategyQuant X (SQX) is a desktop application that generates and backtests strategies for
MetaTrader 5. This project drives **three independent installs of it** on one 48-core machine:

| install | role | port | who may use it |
|---|---|---|---|
| `SQX` (master) | the owner's GUI. Holds the real projects and the data store | — | the owner only |
| `SQX_w1` (conductor) | headless worker for authoring, queries and short jobs | 5060 | agents, freely |
| `SQX_w2` (custodian) | headless worker for the one long job at a time | 5070 | agents, freely, one job |

The workers share the master's `user/data/History` by symlink. Python talks to a worker over an
HTTP API (`sqcli` verbs) or reads its files directly with no SQX running.

### 1.2 What can be driven programmatically

🔬 Verified end to end:

- **Projects can be created, configured and run from code.** A project is cloned from a frozen
  donor, its tasks rewritten, its cross-checks enabled and configured, and the run launched.
- **Strategy files (`.sqx`) can be rewritten.** They are ZIPs; parameter values live in exactly one
  place, `strategy_Portfolio.xml` → `<variable><id>NAME</id>…<value>N</value>`, and the rules
  reference variables by name, so rewriting the value rewrites the rule.
- **Building blocks, random groups, strategy templates and build projects can be authored from a
  plain-English description** by agent skills, validated against the install's own vocabulary
  before import.
- **Databanks can be curated**: strategies removed by identity, so the next task in the chain sees
  only survivors.
- **Everything SQX produces can be read without SQX running** — see §1.4.

### 1.3 What cannot

- ⚠️ **There is no import verb for price data.** `sqcli -data` only exports. Injecting a synthetic
  series (for a Masters-style permutation test) requires the master's GUI, which is the owner's.
- ⚠️ **`saveconfig` output cannot be fed to `loadconfig`** — the verbs are asymmetric.
- ⚠️ **A running instance must never have its `project.cfx` edited on disk**: SQX rewrites the file
  on save and exit and the change is lost silently.
- ⚠️ **Every SQX sync deletes on-disk `.sqx` files not held in memory.** Anything that restarts SQX
  can destroy databanks.
- ⚠️ **No external backtest engine exists.** `strategies/translate/` is empty. A strategy cannot be
  re-evaluated outside SQX, only its *trades* can be re-analysed.
- ⚠️ **No `sqcli` verb changes a strategy's parameters.** The only way to score a chosen parameter
  combination is to write it into a `.sqx` and retest that file — which is exactly what the variant
  factory does.

### 1.4 What comes out, and what it costs to get

| artefact | what it holds | cost |
|---|---|---|
| databank metrics export | 41 aggregate metrics per strategy, with `(IS)`/`(OOS)` columns | seconds |
| trade export | every trade: entry/exit time and price, size, net P&L, **MAE/MFE in account currency**, sample tag, and **exit reason** (`Close type`) | ~90 min for a few thousand strategies |
| `dailyEquity.bin` inside each retested `.sqx` | per-day P&L, per result leg **and per cross-check market** | 🔬 962 variants in **1.5 s**, 5.9 MB of Parquet |
| SPP grid | ~11–15k parameter permutations with full metrics per permutation | the SQX run |
| Walk-Forward Matrix | 30 cells (steps × OOS share), per-step parameters and trades | the SQX run |
| Monte Carlo Retest | 11 confidence levels per metric per task, plus per-simulation P&L vectors | the SQX run |
| M1 bar library | 🔬 `XAUUSD_DukasM1_Infinox` = **7,949,285 bars**, loaded in **0.4 s**; every other timeframe is resampled from M1 and cached | trivial |

Costs per asset (spread, commission, swap, slippage) are declared per symbol in versioned YAML and
are **applied per task**, so a build and its out-of-sample retest carry different costs by design.

### 1.5 The variant factory — the capability worth understanding in detail

This is the piece that makes parameter-space work possible, and it is more capable than "generate
variants" suggests.

1. **Reconnaissance.** An SPP grid (10–15k permutations) is read and reduced to a *design brief*:
   which parameters move the result, which are **provably inert** (the exact-duplicate test, not a
   variance threshold — see §7), each live parameter's marginal curve, its contiguous plateau and
   its centre.
2. **Design.** The brief becomes ~2–5k tuples in three strata: **neighbourhood** (±k level steps
   around the plateau centre, complete), **coarse factorial** (a *complete* grid over fewer levels,
   saturated parameter by parameter in order of variance explained), and **coverage** (scrambled
   Sobol over *every* parameter, frozen ones included). Nothing here is a plain random draw.
3. **Controls.** Five rows exist to fail: the origin rebuilt through the factory, three
   known-result canaries taken from extreme SPP permutations, and one inert pair per frozen
   parameter. A broken chain returns a plausible middling number; extremes catch it.
4. **Fabrication.** Each tuple is written into a `.sqx` by textual substitution — byte-identical
   everywhere the tuple did not reach — with the identifier stamped **inside** the XML (SQX renames
   on collision) and the inherited `<Fingerprint>` removed (or the databank would deduplicate 5,000
   variants into one).
5. **Verification.** The manifest reads the tuples back *off the files* and compares them against
   the plan. Tuple ≠ file is a silent failure in every other arrangement.
6. **Execution and harvest.** Loaded into the custodian, retested in three legs, then the metrics
   panel and the per-day equity curves are harvested.

There is a second, unrelated use of the same machinery: **period rescaling**, which fabricates
siblings of one strategy with bar-unit parameters divided by a timeframe ratio, for the
cross-timeframe test.

---

## 2. The data policy — and the one-way door

Every asset's history is cut into three segments, declared in versioned YAML:

| segment | role |
|---|---|
| `build` | the only sample the generator ever sees |
| `oos1` | everything from the out-of-sample retest to the SPP: decay, Monte Carlo, MC Retest, cross-market, cross-timeframe, SPP |
| `oos2` | **RESERVED** for the walk-forward correlation and the walk-forward matrix — the last two tests |

🔒 **`oos2` is a one-way door and every look spends it.** Steps 7–16 read `oos1` again and again, so
by the time the final tests run it is exhausted; `oos2` is the only untouched data left and it is
fired once. Any proposed test must say which segment it reads, and a diagnostic that reads `oos2`
is almost always the wrong design.

A related rule: **the results of the last three tests are not looked at until all three have been
run**, because seeing two of them contaminates the decision to run the third.

---

## 3. The pipeline — 21 steps

| # | step | where |
|---|---|---|
| 1 | idea, in conversation | — |
| 2 | vocabulary: does the building block exist? if not, author and install it | agent skill |
| 3 | strategy template: fixed block + random hole, with a registry of what has been tried | agent skill |
| 4 | preflight: costs, windows and ranges — **blocking** | `core/assets.py` |
| 5 | create the custom project (cloned from a frozen donor) | `sqx/projects/builder.py` |
| 6 | configure the build | doctrine + YAML |
| 7 | out-of-sample retest in SQX | its own task, `oos1` costs |
| 8 | IS/OOS screening in Python → apply verdict to the databank | `gate/` |
| 9–10 | cross-market retest in SQX, then its analysis | `strategies/crossmarket/` |
| 10.5–12 | rescaled siblings, cross-timeframe retest, then its analysis | `strategies/crossTF/` |
| 13–14 | Monte Carlo Retest in SQX (8 perturbation tasks), then its analysis | `strategies/retest/` |
| 15–16 | the two SPP runs, then the reconnaissance | `strategies/sppUltra/` |
| 16.5 | fabricate and retest the variant batch | `sqx/variants/` |
| 17 | walk-forward correlation | `walkForwardCorrelation/` |
| 18 | CSCV / PBO | `walkForwardCorrelation/pbo.py` |
| 19 | Walk Forward Matrix in SQX | `strategies/walkForwardMatrix/` |
| 20 | **joint reading of 17, 18 and 19 — blind until all three exist** | ❌ does not exist yet |
| 21 | exposure against buy-and-hold | `strategies/exposure/` |

From 22 onwards the portfolio stage begins; it is barely started by design.

---

## 4. What is already implemented

Read the **question** column. The point of this section is that a proposal should either be absent
from it, or be a sharper version of something in it with the difference stated.

### 4.1 Over a whole population (thousands of strategies at once)

| module | the question it answers | how |
|---|---|---|
| `gate/` | of the thousands that were built, which few are worth spending machine time on? | a cascade of eight screens, each run over what the last left: **presence** (dropped by SQX = rejected), **sanity**, **static metrics**, **degradation** IS→OOS, **shape**, **the monkey** (§4.2), then two soft ones — **family** (Benjamini-Hochberg over the survivors) and **redundancy** (are these N strategies or one repeated N times, measured on equity curves). Joins the build and retest databanks on identity, emits a verdict SQX can apply |
| `tasks/analysis/decay.py` | how much of each strategy's in-sample edge survived, and is what is left bigger than its own error bar? | Sharpe either side, retention, Lo's standard error, years positive, share of profit from the best quarter → keep / doubt / discard |
| `tasks/analysis/improvement.py` | does filtering on an in-sample metric improve the out-of-sample outcome, and at what cost in survivors? | every metric swept at the 5/10/20/30/50 % cut from both ends, with a bootstrap interval on the difference; refuses to judge a filter leaving under 200 strategies |
| `tasks/analysis/replication.py` | does a conclusion drawn on one generation hold on another, independently generated one? | outcome gaps, thresholds carried across, rank stability |
| `tasks/analysis/excess.py` | over a family of tests, how many passed against how many chance alone would give? | excess, FDR, and whether the p-values are fine-grained enough to name anyone |
| `tasks/analysis/correlations.py` | which in-sample metric predicts which out-of-sample outcome? | Spearman-led, with the FDR correction across the family |

### 4.2 One strategy, from its trade list

| module | the question it answers | key design decisions |
|---|---|---|
| `nulls/` | how much of this result would a random trader with the same opportunity set have got? | A **ladder** of four rungs — randomise *when each trade is entered*; *when, and how long held*; *when, and the volatility sizing*; *free* (only trade count and cost survive). The gap between consecutive rungs is what that channel was worth. Costs are measured from the trades themselves; the fill convention is measured per strategy (🔬 open-to-open reconciles at **0.999985**) and a p whose run did not reconcile is not read. A verifier proves null-against-null p-values are uniform before any real strategy is judged |
| `strategies/monteCarlo/` | given this trade history, what is the result's shape made of? | Five resampling models in two families — `iid_shuffle`, `block_shuffle`, `stationary` (reorder only) and `iid_bootstrap`, `block_bootstrap` (composition changes) — plus a stress family (missed entries, worse costs, fills degraded toward each trade's own MAE) and a regime family (volatility terciles by ATR or GARCH, calendar slices). Each model's table says what it preserves. **Deliberately unseeded**: stability across independent runs is measured instead |
| `strategies/retest/` | which single perturbed input breaks it? | Reads SQX's eight Monte Carlo Retest tasks: **starting bar, spread, slippage, minimum distance, strategy parameters, exit parameters, OHLC, and all of them at once**. Four questions in order: how much does it hurt (tail quantiles, conditional drawdown), how does it hurt (one regime or two), what breaks it (effect sizes in units of the control), do I believe it (multiplicity paid for) |
| `strategies/crossmarket/` | does the edge transfer to markets it never saw, or was it just being long? | Five placement nulls per market, each declaring what it randomises (block shift within regime and weekday-hour slot; segment permutation; resampled holds; fitted holds; regime strata). Re-derives the fill convention per market and **refuses to interpret a market it could not reproduce**. Carries a cost/execution stress with a breakeven cost multiple |
| `strategies/crossTF/` | does the edge survive being read on a slower clock? | Rescaled siblings run on the new timeframe **and back on their own**, the second being the control that separates "it died on H4" from "it died when its periods changed" |
| `strategies/exposure/` | what did that return cost in market time? | Occupancy, three buy-and-hold sizing conventions at matched risk, return per exposed hour, and how much of the market's move happened while holding |
| `strategies/profitShape/` | how few trades and how few periods does the result rest on; are the trades independent; did the mean change? | `S_top(1 %, 5 %)`, metrics with the best 5/10/20 trades removed, best-3-months and best-year shares, median vs mean · Wald–Wolfowitz runs, Ljung–Box on trades and on daily P&L, longest losing streak against 10,000 shuffles · OLS-CUSUM with both sides, rolling Sharpe with a non-normal band |
| `strategies/entryQuality/` | does the entry itself predict favourable movement, and what does arriving late cost? | MFE/MAE per horizon in ATR units off highs and lows, **e(k) against a band of random entries matched on hour-of-day and long/short split**, reported per direction; and the price given up by entering d bars (and d minutes) late, as a share of gross expectancy and as a multiple of modelled cost |
| `nulls/filter.py` | did a filter beat dropping the same share of trades at random? | Per-trade statistics, empirical p. **Built, tested, and with no consumer yet** — it waits for the ablation work in §5 |

### 4.3 One strategy, across a parameter space

| module | the question it answers | key design decisions |
|---|---|---|
| `strategies/sppUltra/` | which parameters move the result, which are provably dead, and is this family worth 5,000 variants? | Eta-squared reported **as a table over several metrics, never one column**, plus the exact-duplicate test that decides freezing (§7). Contiguous plateaus and their centres. A noise check: the best point must clear what searching a pure-noise grid of the same effective size would produce |
| `strategies/parameterCloud/` | is the chosen point a lucky spike or a plateau; who moves the result; is there a surface at all; does its shape survive being cut into periods? | Rank, plateau fraction and shrunk expectation in a neighbourhood measured in **level steps**; first-order and total Sobol indices computed on a quadratic surrogate; residual roughness *and* a model-free neighbour-disagreement roughness; gradient and Hessian at the origin; per-period profitable fraction, rank persistence, top-decile centroid and its drift; and an equal-weight blend of plateau members spread by farthest-point against the single point |
| `walkForwardCorrelation/` | does in-sample performance predict out-of-sample performance, and is the *way parameters are picked* prone to overfitting? | Rho with an interval that says `indeciso` rather than pretend; **CSCV/PBO over C(12,6) = 924 partitions**, run once per selection rule so the answer is "choosing by plateau centre instead of by maximum takes the PBO from 30 % to 4 %". Deflated Sharpe with an independent-trials count that refuses a cluster split leaving half the variants in one cluster |
| `walkForwardMatrix/` | does what optimises well predict what does well afterwards, or does re-optimising select for failure? | 30 cells (steps × OOS share), rho per cell, optimum drift between steps, verdict predicts / blind / perverse |

### 4.4 Shared statistical libraries

| module | what it holds |
|---|---|
| `core/surface/` | **dedupe**: sentinel removal, distinct tuples, the *effective* n, and a bootstrap that resamples tuples rather than rows · **shift**: Hodges–Lehmann in units, Cliff's delta in rank, QQ curve, tail excess, dispersion ratio · **plateau**: plateau area, half-max area, the noise maximum, the deflated Sharpe, and the rank / plateau fraction / shrunk expectation of one chosen point |
| `core/significance.py` | Sharpe with its shape (skew, raw kurtosis), the variance factor both formulas share, the Probabilistic Sharpe Ratio, and the minimum track-record length |
| `pipeline/` | the chainer: mothers in, verdicts out days later; resumable, with a per-mother ledger and proof that deleting variants loses nothing |
| `ledger/` | **the global search ledger**: one appended line per search over a study's whole life, the funnel it produced, the map of which history has been spent and how often, the pooled N and sigma every deflated Sharpe should be eating, and the frozen thresholds. It also **enforces** the one-way door — a step that may not read a reserved segment is refused, and steps 17/18/19 are not served until all three have run |
| `perf/` | a cost catalogue: what every module costs in time, memory and disk, measured rather than estimated |

---

## 5. Designed, specified, not yet built

Each of these is a self-contained written commission in `docs/encargos/`. They are **not** open
questions — the design is settled; what stops them is named.

| # | what it would add | what blocks it |
|---|---|---|
| 8 | **Built on 2026-09-24** — see `ledger/` in §4.4. What remains of it: each module still reads its threshold from its own `config.yaml`, with `ledger/thresholds.yaml` as a register and a checker that refuses to let the two diverge |
| 9 | **A null population through the entire chain.** 10,000 random-entry strategies pushed through all 21 steps, counting how many come out. "If 4 of 10,000 monkeys arrive and 5 of 10,000 of yours do, you know what that 5 is worth" | depends on 8. Must be done **before** the first real full pass, or the monkey count becomes a number compared against a known answer |
| 10 | **Hansen's SPA and Romano–Wolf StepM** over the surviving population: which strategies beat the benchmark once the whole search is discounted. Complementary to the CSCV, not a substitute — different matrix, different question | depends on 8 |
| 11 | **Edge per trade in cost units**: gross expectancy per trade over mean spread, breakeven cost multiple, cost-to-edge ratio, net expectancy against a cost multiplier, broken down by entry hour | the percentage commission may be charged per leg or per trade — a factor of 2, unmeasured |
| 12 | **Structural tests**: rule ablation, signal inversion, and a seeded random-entry block inside SQX. The XML route is already investigated — ablation is *deleting a `<Block>` from an `<Item key="AND">`*, and SQX declares `oppositeBlockKey` on custom blocks | needs strategy *logic* edited, not values; and D3 needs an integer hash inside a custom block, which the install's vocabulary may not provide |
| 14 | **Conditional performance map**: trades classified by volatility tercile, efficiency-ratio tercile, session and weekday | nothing technical — it is last on purpose, being the only test that *manufactures* hypotheses |
| 15 | **A performance surface per market**, and whether the good regions coincide across markets (Spearman and top-decile Jaccard) | costs unresolved for 16 assets, plus J × markets backtests of CPU |
| 16 | **The trade replay simulator**: re-execute each trade from a shifted entry along the M1 path, recomputing stops and sizing — the honest version of the delay test | the acceptance criterion needs a population with stops to validate against, and this one has none (§7) |
| 17 | **Feed quality and bad-tick attribution**: spikes, spike-and-revert, stale runs, gaps; then what share of profit sits within ±w bars of an anomaly | thresholds are the owner's to fix, in advance |
| 6 | Block taxonomy: labelling the 767 pooled building blocks by family | nobody has run it |
| 13 | Alpha/beta decomposition | **parked by the owner**, deliberately: the individual sequence closes first, and the factor that would matter most (returns of EAs already trading) does not exist yet |

---

## 6. Hard constraints — read before proposing

**Methodological, and not negotiable:**

1. **Diagnosis, never selection.** Clouds, variants and clones are used to measure rank, plateau
   size, sensitivity, stability and transfer. Replacing the chosen strategy with the best-scoring
   clone produces a *more* overfit result with a smaller effective sample. Any parameter move is a
   human decision, logged, and revalidated on untouched data.
2. **No new filter comes out of a diagnostic** without being logged as a new trial and revalidated.
   With enough diagnostics, something always looks significant.
3. **Thresholds are frozen before the data is read.** A threshold set after seeing the numbers is
   not a threshold. Agents may read the threshold file, never edit it.
4. **`oos2` is spent by looking at it** (§2).
5. **The owner's own SQX projects are his.** What a master project builds is a decision, never a
   bug to fix and never a finding to report.
6. **Costs are per task and declared per asset.** A test that quietly reuses one project's costs
   for another window is unattributable afterwards; every run happens in its own custom project.

**Technical:**

7. **The dependency set is small and pinned**: numpy, scipy, pandas, pyarrow, matplotlib, PyYAML,
   ruamel.yaml, arch, diptest, Flask, Markdown, and PySide6/FastAPI for the desktop app.
   **No scikit-learn, no statsmodels, no numba, no ruptures, no SALib.** Proposals that need one
   must say so and justify the install; anything reachable with scipy should use scipy.
8. **No import of synthetic price data** (§1.3), so bar-permutation tests in the Masters sense are
   not practicable today. The project's answer to that question is the monkey population (#9).
9. **One data vendor.** Dukascopy for everything but the Brent, so no cross-vendor data check is
   possible — which is exactly why #17 exists.
10. **One machine, and its limit is memory bandwidth, not cores.** 🔬 Two AMD EPYC 7413 sockets:
    96 logical threads but **48 physical cores**, and SMT *costs* throughput on this workload
    (211,419 paths/s on 48 physical against 203,617 on 96 logical). A compute-bound control that
    fits in L1 scales **46.1×** with 95 processes; the real out-of-cache kernel scales **18.3×**
    with the same 95 — the cores sit waiting for DRAM. Of 128 GB, the master JVM claims 71, the
    custodian is allowed 80, Python gets about 20 and the OS 10–12. **A proposal whose cost is
    "more simulations" is usually bounded by memory traffic**, and the fix that has worked here was
    restructuring the kernel to work in strips: 84× less memory and 3.6× faster at once.
    Several sessions share the two workers, so a long job is announced before it starts.

---

## 7. Measured facts that constrain any new design

These are all 🔬 measured on this install, with the source named. Several of them have already
killed an obvious-looking test.

**About the parameter space**

- **Two SPP runs cannot be paired.** The in-sample run and the out-of-sample run of one strategy,
  byte-identical settings, share **6 tuples out of ~11,600**. Nothing can compare two SPP windows
  directly — which is the entire reason the designed variant batch exists.
- **Eta-squared of a provably inert parameter is not zero — it is biased upward.** `CBlock_SqzMmnInt21`
  gives 217 groups of tuples differing only in it and **all 217 produce an identical backtest**, yet
  it scores 0.0173, above any freezing threshold one would pick, because an SPP samples unbalanced.
  The converse also fails: a parameter scoring 0.0016 is demonstrably live. **Freezing is decided by
  the exact-duplicate test; variance explained only allocates levels.**
- **Rows are not observations.** Inert parameters duplicate points and the surface is smooth on top
  of that, with lag-1 autocorrelation up to **+0.89**; an interval over 12,000 correlated rows is
  falsely narrow by roughly a factor of three.
- **`RExpectancy` carries sentinels** — 99999.0 on 3 rows, −1.0 on 15 — which are 0.08 % of a grid
  **and win the argmax over 5,000 variants**.
- **The PBO of pure noise has a standard deviation of 0.21** over 252 partitions; individual draws
  ran 0.25 to 0.92 with a mean of 0.52. A grid at 0.45 and one at 0.55 are not distinguishable.
- **Regressing the chosen variant's out-of-sample Sharpe on its in-sample Sharpe measures a seesaw,
  not decay**: it reads −0.57 on pure noise and −0.99 on a panel with a genuine edge, i.e. *more*
  negative where the edge is real.
- **An unconstrained cluster count flatters the deflated Sharpe.** The silhouette prefers splitting
  479 variants 478-against-1, which counts as two trials; refusing any split that leaves half the
  variants in one cluster gives 21 trials, and a deflated Sharpe of 0.66 instead of 0.91.

**About this corpus of strategies**

- The generated XAUUSD population carries **no stop, no target and no trailing**. 🔬 Across 960,705
  exported trades the exit reason takes exactly three values: `Exit After X Bars` (720,874),
  `Exit Signal` (187,853), `End Of Friday (Time)` (51,978).
- One studied strategy is **entirely long** — 1,119 of 1,119 trades.
- **Only 51.0 % of 757 strategies beat their entry-timing null on Sharpe, and 21.5 % on net
  profit.** The statistic moves the verdict more than the null does: real trades are **36 % less
  volatile** than random ones (551 $ vs 720 $ per trade, skew +0.54 vs −0.77, kurtosis 6.8 vs 27.1),
  and Sharpe rewards being calmer than chance while net profit does not.
- On that same corpus, **the e-ratio of a studied strategy sits inside the 5–95 % band of matched
  random entries at every horizon tested**, and below it at k=1. Its profit is 99 % from one year,
  and its best 5 % of trades carry 405 % of the total.
- **The CUSUM can call a series stable while its halves differ by a factor of sixteen** (+82.5 vs
  −5.1 per trade, supremum 1.01 against 1.36). At per-trade dispersion of hundreds of dollars the
  test has very little power.
- **Half a variant batch barely trades**: 1,002 of 2,000 rows under 30 trades, and filtering them
  out collapses one parameter to a single value — that parameter chooses between trading and not
  trading, not between good and bad.

**About the data and the exports**

- **1.2 % of XAUUSD entries do not land on a bar open** (far more on other projects): pending orders
  filled inside a bar, which is a price-conditional selection any bar-grid study must measure before
  trusting its comparison.
- **The fill convention is open-to-open**, measured per strategy at a correlation of 0.999985
  against SQX's reported P&L; the runner-up convention reads 0.9629.
- **Costs are recoverable per trade** as `gross − reported P/L` — but ⚠️ **the spread is inside the
  fill prices and does not appear in that residual**, so what is recovered is the commission (and
  swap overnight), not the spread.
- **A Monte Carlo Retest stores only a P&L vector per simulation** — 4 bytes per trade, no dates, no
  prices, no sizes, and **not the spread that was drawn**. Checked on 4,896 of 4,896 files.
- **A confidence level is an order statistic per metric, not a scenario.** The net profit and the
  drawdown on the "95 %" row come from different simulations; no row of that table is a coherent
  equity curve.
- **Names do not identify strategies**: two databanks of one project hold entirely different
  strategies under the same name, and 45 of 231 strategies had byte-identical trades under different
  hashes. Identity is the SHA-256 of the **normalised** inner XML — the raw hash matched 0 of 115
  build-to-retest pairs, the normalised one matched 115 of 115.
- **The M1 library is clean where it is easy to check**: 0 OHLC inconsistencies in 7.9 M bars, but
  40,097 flat bars (0.50 %) whose distribution nobody has looked at.

---

## 8. Where the holes are

An honest list, in case it suggests something.

1. **Step 20 does not exist.** There is no module that reads the walk-forward correlation, the CSCV
   and the walk-forward matrix *together* and issues one verdict — and by design none of the three
   may be looked at until all three have run.
2. **The global ledger now exists, and it is empty.** Only one study has been reconstructed into it
   (120 → 45 in eight screens) and, of its eight searches, **one** recorded the distribution of its
   candidates — a funnel stores counts, not scores. So the accumulated N is still the N of one gate
   run until the chain starts recording as it goes.
3. **The portfolio stage is barely started.** What is agreed: correlation between equity curves and
   not between metrics; drawdown computed on the aggregate, never summed; prop-firm rules are
   constraints, not after-the-fact filters. Everything else is open.
4. **Nothing measures redundancy against strategies already trading live**, because there are none
   yet. This is what parks the alpha/beta work.
5. **No test yet distinguishes "the entry is worthless" from "the exit is doing the work"** in a way
   that can be *acted* on — the e-ratio says the first, but the controlled comparison (the same
   exits with random entries, inside SQX) is commission #12 and unbuilt.
6. **Five analysis steps have no agent skill**, so the chain cannot run end to end unattended:
   cross-market (10), MC Retest (14), SPP reconnaissance (16), WFC (17) and CSCV (18).
7. **Costs are unresolved for 16 of 17 assets**, which blocks every multi-market design.
8. **Nothing checks the strategies against a market microstructure model** — no order-book
   assumptions, no partial fills, no queue position. Every fill in this project is an open price
   plus a modelled cost.

---

## 9. What a useful proposal looks like

Not a constraint on creativity — a way of making an idea checkable against everything above. A
proposal that answers these seven lines can be costed and built; one that does not usually turns
out to be item 4.2 in a new hat, or to need data that cannot be imported.

| | |
|---|---|
| **the question** | in one sentence, and it must not already be in §4 — or, if it sharpens one, say what the difference buys |
| **unit of observation** | a trade, a bar, a strategy, a parameter tuple, a market, a period. This decides everything else |
| **input** | which artefact of §1.4, and whether it already exists or needs an SQX run |
| **segment** | `build`, `oos1`, or — with an explicit justification — `oos2` |
| **cost** | Python seconds, or SQX hours; if the latter, why it is worth a custodian slot |
| **diagnostic or gate** | and if a gate, what the threshold is and why it can be frozen before looking |
| **failure mode** | what result would make the test *wrong* rather than merely negative. A test nothing can falsify measures nothing |

Two habits of this project worth borrowing in any proposal:

**Reconcile before interpreting.** Every module that prices something re-derives what SQX already
computed and refuses to speak if the two disagree — the fill convention at 0.999985, the canaries
in a variant batch, the manifest read back off the files. Every one of those checks has caught a
real failure that produced plausible numbers.

**Say what the null holds fixed.** Every randomisation in this codebase carries a table of what it
preserves and what it hands to chance, printed next to the numbers it produced. A null that changes
two things at once cannot attribute a result to either.
