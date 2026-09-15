# strategies/crossmarket — does the edge transfer to markets it never saw?

One study, one folder. Inside it, four boundaries in the order the data flows, as rule 5 of
`CODESTYLE.md` requires: **configuration → modelling → execution → inference**. Read
`POSSIBLE_IMPROVEMENTS.md` before extending any of this.

```
config.yaml ─▶ markets ─▶ envelope ─▶ trade_models ─▶ backtest ─▶ metrics ─▶ charts
 every knob    what it     the real    how random      prices        what a      the
               runs on     run's shape  runs are drawn  every run     run is      picture
                                                        in dollars    worth
```

**This study issues no verdict, and it never drops a market.** Every market the export carried is
reported in full, with the reasons to distrust its numbers named beside it. Which strategy to keep
is the owner's call, made outside here. That is a change from the first build, which gated markets
out of a vote and cost a Brent result at p = 0.005 because 8% of its entries were pending fills.

**`explorer/` is the only way to run it, one strategy at a time.** Nothing is written to disk and
nothing is cached: every number on the panel comes from the run the owner just started. There is no
batch command and no report file — that was removed on 2026-09-15 at his request, because a stored
result can always be read as an answer to a question it was not computed for.

**Every random run is priced in dollars, with the real trades' own sizes and costs.** That is what
lets the study report net profit, drawdown, Ret/DD, Sharpe and profit factor rather than one
abstract statistic: measured, the P&L reconstructed from the bars correlates **0.9996** with the P/L
SQX itself reported, so the real equity curve on the panel is SQX's own.

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.py` | Reads `config.yaml`: every tunable of the study, in one place | imported | overrides → config |
| `markets.py` | Reconciles what the export really carries against what `markets.yaml` declares | imported | asset + export → universe |
| `envelope.py` | The real run's shape on the bar grid: bars held, gaps, regime blocks, the weekday-hour groups a model may move it to, and the bars to each Friday close | imported | trades + bars → the market dict |
| `pricing.py` | ATR, the cost SQX charged recovered per trade, the fill convention re-derived by reconciling against SQX's own prices, and the long-only assertion | imported | bars + trades → returns, cost, convention |
| `holdfit.py` | Fits a discrete distribution to the real holds and gaps, and says whether it fits | imported | counts → sampler, goodness |
| `sweep.py` | **The window sweep.** Calendar blocks of each size, the trades and free room in each, and a free-placement model confined to them | imported | bars + trades + model → blocks, entries, holds |
| `strata.py` | The regime state of every bar — ATR quantile × trend sign — for the optional `regime_strata` model | imported | bars → stratum index |
| `trade_models.py` | **How random trades are drawn.** Five models behind one signature, what each holds fixed, and the Friday truncation every one of them gets | imported | envelope → entries, holds |
| `backtest.py` | Prices the real run and N random ones identically, in dollars, in batches | imported | fixed + bars + model → table, shapes, cone |
| `metrics.py` | **What a run is worth.** Net, drawdown, Ret/DD, Sharpe, PF and the losing run of thousands of runs at once, each with its own good side | imported | P&L matrix → statistics |
| `equity.py` | Equity through the sample on the **calendar**, and the percentile cone around the real curve | imported | P&L + exit bars → curves, bands |
| `inference.py` | Every reason to distrust a market, which test a result actually is, whether a sweep point has the power to be read, and which way a sweep curve goes. **It decides nothing** | imported | row, blocks, points → warnings, power, trend |
| `paired.py` | **Test 1b.** Each trade against the exact mean of every window of its own length in its own regime block. Needs no null model and no cost assumption | imported | fixed + bars → alpha, Wilcoxon p |
| `exposure.py` | **Test 1c.** Concentration E — withheld where the market has no drift — drift-neutral excess A with a hold-weighted bootstrap CI, and the MFE capture ratio | imported | fixed + bars → E, A, capture |
| `drivers.py` | **PDF §5.4.** What kind of market this is: Hurst, variance ratio, ADX trend share, ATR%, efficiency ratio | imported | bars → profile |
| `significance.py` | Minimum track-record length and bootstrap CIs on PF and expectancy. No DSR — see `POSSIBLE_IMPROVEMENTS.md` | imported | returns → moments, CI |
| `breadth.py` | Breadth, worst-market floor and PF dispersion across one strategy's markets | imported | per-market rows → breadth, floor, CV |
| `fingerprint.py` | Behavioural fingerprint against the base asset: holding-time KS, MAE/MFE by ATR, return shape | imported | trades + bars → fingerprint |
| `stress.py` | Cost gradient, breakeven cost multiple, and decay under a bar shift or range slippage | imported | fixed + bars → cost/slippage curves |
| `correlation.py` | Weekly equity curves, their correlation matrix, and PCA by SVD across a strategy's markets plus the base asset | imported | curves → correlation, variance share |
| `bootstrap.py` | Block-bootstrap resampling and percentile confidence intervals | imported | a sequence → resampled positions, a CI |
| `charts.py` | The two simulation figures as inline SVG: a statistic's distribution with the real run on it, and the equity cone | imported | numbers → SVG |
| `figures.py` | The per-market comparison figures: one bar or one cell per market, and the window sweep's p curve | imported | rows → SVG |
| `tables.py` | Renders every test into HTML tables for the panel's tabs and the static report | imported | rows → HTML |
| `panel.py` | The market table, the diagnostics table, the glossary and the Spanish wording | imported | rows → HTML |
| `explorer/` | The interactive panel — the only entry point. See `explorer/README.md` | `python3 -m strategies.crossmarket.explorer.serve --project XAUUSD --databank "Retest Markets - Family" --asset XAUUSD --export 2026-09-14` | export → `http://127.0.0.1:8766` |

## What a random run is worth, and in what unit

`metrics.py` computes the same eight statistics for the real backtest and for every random one, plus
`mean_r` — the mean log return per trade over the market's median ATR, which is the one figure that
compares across markets. Each carries its own direction: for `dd` and `losing_run` a **small p means
the real run suffered less** than chance, the opposite of how `net` reads, and the tables say so on
every row.

Column k of a random run reuses real trade k's **size and charged cost**. So a random run is the
same money at risk, paying the same broker, differing only in when it entered. The wrap-around in
`backtest.price()` is there for a model that draws more trades than there really were; none ships
today, and `POSSIBLE_IMPROVEMENTS.md` §1 still lists varying the trade count as worth trying.

The cone is drawn on **calendar time**, not trade number: random runs place their trades at different
moments, so that is the only axis on which their curves and the real one describe the same stretch of
market. `equity.py` bins each trade's P&L into the step its *exit* falls in, because that is when the
money is realised.

`backtest.py` never chooses a model and `inference.py` never produces a number it judges. That is what
lets the same runs be re-judged, or the same judgement re-run under another model, without editing
either — which is the only way to find out whether a conclusion depended on an assumption.

## The markets are discovered, and only classified by hand

`markets.yaml` groups each base asset's markets into categories — `family`, `structure`, and whatever
comes next. **It classifies; it does not decide what exists.** What a strategy was really retested on
is read from the export, whose `trades/<feed>/` folders are built from the trades' own `Symbol`
column. A feed the declaration does not name is kept and marked `sin clasificar`; a declared feed the
export has no trades for is printed as absent at start-up. Before this, a mismatch showed up as a
market with zero strategies rather than as an error.

The list is still fixed before results are looked at: choosing markets after seeing where the
strategies work turns the test into a selection.

## Adding a model

Write a function in `trade_models.py` with the shared signature — `(held, market, draws, rng)` in,
`(entries, holds)` out — add it to `MODELS`, and add a row to `RANDOMISES` saying **what it
randomises**. Nothing else changes: the drawer picks it up and the test explorer gains an entry.

That row is not documentation, it is the finding. A model that randomises more than one thing cannot
attribute a low p-value to any single cause, so the report prints it next to every p-value it produced.

| key | shown as | randomises | what it adds over the one above |
|---|---|---|---|
| `segment_permute` | Shuffled Sequence | placement, order, clustering and regime | the starting point: the real rhythm, re-laid anywhere in the sample |
| `resampled_holds` | Resampled Sequence | the above, plus which holds occur and time in market | drops the multiset, so total time in market varies between runs |
| `fitted_holds` | Fitted Distributions Sequence | the above, plus the holding times themselves | the holds no longer come from the real ones at all |
| `block_shift` | Calendar Shift | **only** placement, inside the regime block and the weekday-hour slot | not a member of that family: it is the one that changes exactly one thing |
| `regime_strata` | Regime Strata | placement, inside bars of the same ATR quantile and trend sign; frees weekday, hour and clustering | **off by default**, runs only when `nulls.models` lists it. Holds the regime by state rather than by a calendar block of arbitrary length |

**These are two families, not four points on a scale.** The first three lift the whole run and drop
it anywhere in the 22 years, so they change *when*, the *order*, the *calendar* and the *regime* all
at once — a low p under any of them cannot be attributed to any one of the four. `block_shift` moves
each trade separately, by whole weeks, inside its own semester and onto its own weekday and hour, so
the regime, the calendar and the clustering all survive. That is why `nulls.headline` names it and
why the summary table reports its p, whatever order the panel shows them in.

🔬 **`renewal` was retired on 2026-09-15.** It rebuilt the occupancy from scratch, walking the bars
and entering with the empirical hazard, so the trade count was random too. On paper that added
something; measured over 8 (strategy, market) pairs it added **nothing** — the same null width as
`resampled_holds` to within 2% and the same p to within 0.004, every time. Once placement is free
across the whole sample, which decade a run lands in dominates everything else, and the first three
already randomise that identically.

The registry keys are the contract — `config.yaml`, `MODELS` and every docstring share them —
and `panel.NAMES` is the only place a reader's name for one lives.

### The window is the backtest's, not the bar file's

🔬 **Every market is sliced to the backtest's own span before anything is computed** —
`envelope.window(trades, bars)`, called once in `explorer/analysis.py`. A bar file runs wider than
the retest that was run on it: measured, XAGUSD bars cover 2003-2026 against a 2008-2022 backtest, so
**a third of the file sits outside it**. Without the slice, a null model places trades in years the
real strategy never saw, with their own drift and their own volatility regime; the drift in Test 1c
is measured over the wrong period; Test 1b's blind window averages bars the strategy never had access
to; the market profile in `drivers.py` describes the wrong stretch; and the equity axis spans years
where the real curve is flat by construction.

Everything downstream inherits the slice because it is applied to `bars` before `backtest.setting()`.
Each strategy gets its own window, since two strategies in the same databank need not cover the same
period.

### Which of them is hardest to beat, measured

🔬 With the window bounded, `block_shift` returns the **lowest p in 7 of 8** (strategy, market) pairs
and the **narrowest null in 5 of 8**. So it is usually, but not always, the one that flatters a
strategy most — and it is never the reason to trust a result. It is the *attributable* model: the
only one whose low p can be read as "the entry timing carried information" rather than "the run
happened to land somewhere kinder".

An earlier measurement, taken before the window was bounded, made the gap look far larger and
systematic (σ 0.073 against 0.095, lowest p everywhere). Most of that was the artefact: the other
three were roaming a third more sample than the real backtest ever touched. **Both readings are
recorded because the first one was published and acted on.**

The practical rule is unchanged: **a strategy that survives all four says more than one that survives
only `block_shift`**, and a lone `block_shift` pass is the weakest of the cases, not the strongest.

### The three free models overlapped their own trades until 2026-09-15

🔬 `trade_models._lay` offset each trade by its **own** hold instead of the previous trade's, so a long
hold followed by a short one landed on top of it: **1-7% of the trades of every random run overlapped
another**, under all three free models, on every (strategy, market) pair measured — against a
docstring that said non-overlap held by construction. It also let the tail of a run that did not fit
wrap round onto its own head. Both are fixed: trade k opens gap k bars after trade k-1 closes, and a
trade that would wrap onto the start of its sequence or run past the last bar is dropped, the way a
Friday cut already drops one.

Re-measured on the same 8 (strategy, market) pairs at 10,000 draws: p moved by at most **0.009**
under `segment_permute`, 0.004 under `resampled_holds` and 0.005 under `fitted_holds`; σ by at most
2%. `block_shift` does not use `_lay` and came out identical to the digit. The measurements earlier in
this file were taken before the fix: a shift that size can reorder two models whose p differed by less
than 0.01, and nothing larger.

🔬 **`block_shift` still overlaps**: 2.5% of trades on XAGUSD and 1.7% on Brent (Strategy 1.10.80),
because trades in different weekday-hour groups wrap by different numbers of weeks. It was left as it
is on purpose — the owner fixed it as the reference the window sweep is read against — and is recorded
here rather than changed.

## The window sweep — how much of a free-placement p is regime

`segment_permute`, `resampled_holds` and `fitted_holds` re-lay the rhythm anywhere in the window, so
they destroy three things at once: the **regime** a trade lands in, its **calendar**, and the
**clustering**. The sweep re-draws those three inside consecutive calendar blocks of shrinking size
(`sweep.windows`, default `full, 3y, 1y, 6m`): each block's real trades are handed to the model as if
the block were the whole window, and no trade may leave its block. Shrinking the block hands back the
regime and nothing else — calendar and clustering stay destroyed at every size — so p against block
size is a decomposition:

| null | regime | calendar | clustering |
|---|---|---|---|
| free placement, full window | destroyed | destroyed | destroyed |
| free placement, shrinking window | ← restored | destroyed | destroyed |
| `block_shift` (reference, untouched) | kept | kept | kept |

p that stays low as the block shrinks is timing; p that climbs is a pass the regime was carrying. **The
curve never converges on `block_shift`**, which also keeps calendar and clustering: that is another
axis, drawn as a flat reference line, not a destination.

- **`full` is the model itself, draw for draw.** `sweep.confine()` with one block calls the model on
  the same arrays with the same generator. `tests/test_sweep.py` checks the arrays are identical, and
  on real data the swept p and σ matched `backtest.run()` to the last digit on 6 of 6 (model, market)
  pairs, so the panel reads the full point from the model's own run instead of drawing it twice.
- **Blocks are `envelope.blocks()`**, so `6m` is exactly the partition `block_shift` moves trades
  inside. The first and last block are usually partial. A trade's hold is capped at its block's end.
  Sizes are calendar durations; the tables print them in H1-equivalent bars, since the bars are M30.
- **Power is checked, not assumed** (`inference.sweep_power`). A block with fewer than
  `sweep.min_trades` real trades, or less than `sweep.min_free_share` of its bars free, is weak. A size
  whose weak blocks hold more than `sweep.max_weak_share` of the trades is **withheld** — drawn as a
  cross, never as a number — and a size under `sweep.min_months` is never computed. Beside every p the
  power table prints blocks, trades per block, free room, σ of the null and live trades per run.
- 🔬 **The live trade count moves with the size under two of the three models.** `resampled_holds`
  and `fitted_holds` draw a total time in market that can overflow a block, and what overflows is
  dropped; more blocks, more drops. Measured on XAGUSD, Strategy 1.10.80: 98.4% of trades live at
  full, 96.7% at 3y, 95.3% at 1y, 94.1% at 6m. `segment_permute` keeps its multiset and stays above
  99.6%. It is the one thing besides the regime that changes along the curve, which is why the count
  is printed beside every p.
- **The caption is not the reading.** `inference.sweep_trend()` compares the widest and the narrowest
  computed p: `regime` when p climbs more than `sweep.evidence_drop` orders of magnitude, `timing`
  otherwise, `no_pass` when no size reaches alpha, `unassessable` with fewer than two points.
- 🔬 **Measured**, 6 strategies × 2 markets × 3 models at 10,000 draws: 7 curves `timing`, 29 `no_pass`,
  0 `regime`. The one clear pass, Strategy 2.29.29 on XAGUSD, holds p between 0.0009 and 0.0030 at every
  size. Strategy 14.15.26(2) climbs steadily as the block shrinks on both markets — Brent 0.075 → 0.117,
  silver 0.105 → 0.139 — which is the regime shape, just never under alpha. Strategy 15.17.41 on silver
  was withheld at 6m: 13% of its trades sit in weak blocks.
- **It costs time**: nine more nulls per market. One strategy over two markets at the default 25,000
  draws now takes 36-52 s, against about 25 s before.

`regime_strata` is the alternative the owner asked for alongside, built apart and off by default: it
fixes the regime by **state** — each trade moves to a random bar of its own ATR quantile × trend-sign
stratum, read before the bar opens — instead of by calendar proximity. It shares nothing with the
sweep and never runs inside it.

## What the test compares, and what it cannot

The statistic is the **mean log return per trade, net of cost**, divided by one constant per market
(the median ATR as a fraction of price) so markets compare. That constant is identical for the real
run and every random run, so it cannot move a p-value — it only puts gold, silver and Brent on one
axis.

The earlier design divided each trade by the ATR **of its own entry bar**. That is wrong here and was
removed: real entries are chosen by the rule and random ones are not, so any filter that favours
compressed bars divides the real trade by a small number while the move that follows reverts to normal
volatility. It inflates the real statistic with no directional edge at all, in the direction of
passing. `atr_ratio` in every row is the diagnostic that would have caught it.

**Test 1b is the one that needs nothing.** No null model, no cost assumption — cost appears on both
sides of the difference and cancels. It is also the only test here whose reference is exact rather
than sampled: the mean of *every* window of that length in that regime block, not a sample of them.
The source note's literal version — each trade against a passive long over the identical window — is
degenerate for this family: these strategies carry no stop and no target, so their trade return *is*
that passive long, and the difference would be zero by construction.

## Why block_shift is shaped the way it is

Three properties, each of which was needed, and two of which were found by measuring:

- **Blocks**, because thirteen years of gold are not one regime. A strategy whose trades sit in a
  strong trending stretch would beat a null spread over the whole sample on drift alone.
- **Whole weeks, in the block's own weekday-hour groups**, so entries land on the weekday and hour they
  really used — an eight-bar hold entered late on a Friday spans the weekend gap and one entered on a
  Tuesday does not. `calendar_kept` must read 1.00; when the shift was written in bar space it read 0.05.
- **The wrap**, because a strategy's trades span nearly the whole of every block. Placing them end to
  end left one legal position in most blocks and none in nine of twenty-four, and the null then
  reproduced the real run — measured, it returned p ≈ 0.5 for everything.

On top of that, every model's holds are re-cut at the Friday close, because that is an exit rule the
strategies really have (5.4% of all trades in the sampled databank) and it is a rule of the calendar,
which a null can reproduce exactly. `Exit Signal` — 16.6% of trades — is not reproducible without the
`.sqx`, and that is why those strategies are reported as a joint entry-and-exit test.

## Rules these enforce, because each one has a direction

- **A market is never dropped.** It is reported with its warnings. Losing 100% of a market's evidence
  over 8% of its trades was the first build's worst habit.
- **The base asset never counts as evidence.** It is reported as the reference case: on the market it
  was optimised on, a strategy beats its null and its paired benchmark by construction. That says the
  code works, and nothing about the strategy.
- **E is withheld where the market has no drift.** Measured: Brent's drift is t = −0.11, which turned
  the market with the strongest A of the three into E = −69.4.
- **A confidence interval brackets the estimator it is an interval for.** A's bootstrap is weighted by
  holds because A itself is pooled over occupied bars; unweighted, it sat 9% away from its own point
  estimate.
- **Long only.** `pricing.require_long_only()` refuses anything else rather than silently flipping a
  sign. Checked: all 92,329 trades of the 30-strategy sample are Buy.
- **Read the luck figure before any p-value.** It is a scale for reading a table, not a rule.
