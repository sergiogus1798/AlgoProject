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
| `trade_models.py` | **How random trades are drawn.** The registry, the Friday truncation every model gets, and the two that randomise placement only — `block_shift` and `regime_strata` | imported | envelope → entries, holds |
| `free_models.py` | The free-placement family: the three that re-lay the whole run anywhere in the window | imported | envelope → entries, holds |
| `joint.py` | **The joint null.** One a-priori statistic over the out-of-sample markets and one p, pooled from draws that displace every market together | imported | runs → joint p |
| `backtest.py` | Prices the real run and N random ones identically, in dollars, in batches | imported | fixed + bars + model → table, shapes, cone |
| `realrun.py` | The real backtest's own statistics — over **everything SQX reported** and over the grid-locatable subset, which are not the same population — and the mechanical checks | imported | fixed + bars → stats, checks |
| `metrics.py` | **What a run is worth.** Net, drawdown, Ret/DD, Sharpe, PF and the losing run of thousands of runs at once, each with its own good side | imported | P&L matrix → statistics |
| `equity.py` | Equity through the sample on the **calendar**, and the percentile cone around the real curve | imported | P&L + exit bars → curves, bands |
| `inference.py` | Every reason to distrust a market, which test a result actually is, whether a sweep point has the power to be read, and which way a sweep curve goes. **It decides nothing** | imported | row, blocks, points → warnings, power, trend |
| `paired.py` | **Test 1b.** Each trade against the exact mean of every window of its own length, near it in time — a centered window or the regime block, and the test is run under both | imported | fixed + bars → alpha, Wilcoxon p |
| `exposure.py` | **Test 1c.** Drift-neutral excess A with a hold-weighted bootstrap CI, its risk-normalised form, and concentration E with a Fieller interval | imported | fixed + bars → A, E |
| `fieller.py` | The interval of a ratio whose denominator can be zero: unbounded when it is, instead of a number that looks decided | imported | moments → interval |
| `units.py` | One log return in every unit a reader needs: bps, per cent, ATR units, dollars per trade and dollars accumulated | imported | logret → units |
| `curves.py` | Each market's equity on its own real calendar, and what it returned once every market risks the same | imported | fixed → curve, factor |
| `execution.py` | What a worse broker would charge, per feed, from `execution.yaml`; and that file against what SQX really charged | imported | feed + trades → shock, depth, gap |
| `portfolio.py` | **The Portfolio tab.** Every market as one account, what each one adds to it, how often they overlapped, and two ways of asking how much is luck | imported | streams → account, marginal |
| `views.py` | The two views that need more than one market, rebuilt whenever one market is re-run alone | imported | weekly + streams → correlation, portfolio |
| `significance.py` | Minimum track-record length and bootstrap CIs on PF and expectancy. No DSR — see `POSSIBLE_IMPROVEMENTS.md` | imported | returns → moments, CI |
| `breadth.py` | Breadth, worst-market floor and PF dispersion across one strategy's markets | imported | per-market rows → breadth, floor, CV |
| `fingerprint.py` | Behavioural fingerprint against the base asset: holding-time KS, MAE/MFE by ATR, return shape, MFE capture, and the four overlaid histograms | imported | trades + bars → fingerprint |
| `stress.py` | Cost gradient, breakeven cost multiple, and decay under a bar shift or range slippage | imported | fixed + bars → cost/slippage curves |
| `correlation.py` | Weekly equity curves and their correlation matrix across a strategy's markets plus the base asset | imported | curves → correlation |
| `bootstrap.py` | Block-bootstrap resampling and percentile confidence intervals | imported | a sequence → resampled positions, a CI |
| `charts.py` | The two simulation figures as inline SVG: a statistic's distribution with the real run on it, and the equity cone | imported | numbers → SVG |
| `figures.py` | The per-market comparison figures: one bar or one cell per market, and the window sweep's p curves — every swept model on one axis | imported | rows → SVG |
| `overview.py` | The main tab's tables: every market's real backtest, the same at equal risk, and what its sample size holds up | imported | rows → HTML |
| `overlays.py` | The two figures that lay several series over one axis: market equity curves, and two distributions through each other | imported | curves, bins → SVG |
| `alerts.py` | Every warning in four parts: what fired it, what it affects, what it does **not**, and what to do | imported | row → HTML |
| `tables.py` | Renders every test into HTML tables for the panel's tabs | imported | rows → HTML |
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

## The panel opens on the backtest, not on a test

Rebuilt 2026-09-16 at the owner's request. `Resumen`, `Significancia` and `Correlación` were three
tabs answering one question between them, and nobody reads a strategy's drawdown on one page and its
confidence interval on another: they are now one tab, **`Backtest`**, which the panel opens on.

It carries, in this order: the strategy's tiles; every market's **real** backtest (net, return,
drawdown in dollars and per cent, Ret/DD, Sharpe, PF, losing run) with the base asset last and
marked *reference, not evidence*; the same comparison **at equal risk**, every market rescaled until
its worst drawdown is `equity.risk_target_dd` of the account; the **overlaid equity curves**, each
market on its own independent account, in per cent, on real calendar dates so a market whose
backtest starts later starts later on the chart; the correlation matrix; what each test said; what
holds those numbers up; the warnings; the mechanical checks; and a paragraph per statistic.

**What was removed, and why.** `drivers.py` and the `El mercado` tab: the edge-driver regression it
was built for needs six or more markets on the right-hand side and the owner will have four, so with
two it described markets rather than saying anything. `correlation.pca()` and the `Correlación` tab:
with two or three streams PC1 is close to a function of the mean pairwise correlation and added no
axis the matrix did not already carry. Both are recorded as **discarded with a reason** in
`POSSIBLE_IMPROVEMENTS.md` rather than deleted from it, so neither is proposed again from scratch.

## Does adding a market break the portfolio?

The `Portfolio` tab, built 2026-09-16 and named in English at the owner's request 2026-09-17. The retest asks whether the edge transfers; this asks the
question that follows from it — *oil and the Nasdaq need not be brilliant, but they must not wreck
what gold does.* One account of `equity.starting` for every market at once, the base asset included
as the core position, and the drawdown computed on the **combined** curve, never summed from the
parts, as `portfolio/CLAUDE.md` requires.

The table it exists for is **marginal contribution**: the whole portfolio, the portfolio without
each market, and the difference on every statistic. A market whose Δ Ret/DD is negative is costing
the combination more than it brings, however good its own p-value was. 🔬 Measured on
`Strategy 2.29.29`: gold +2.70, silver −0.19, Brent **−4.55**.

Two different ways of asking how much of it is luck, because they are not the same question:
**calendar-block resampling** (`portfolio.block_weeks`, default four weeks) draws whole weeks, so
every market's trades inside a block travel together and a week that was bad for two markets at once
stays bad for both — resampling single trades would destroy exactly the dependence being measured;
and **reordering**, delegated to `strategies.monteCarlo.model.draws`, which leaves composition untouched
so net profit is invariant by construction and only the path statistics move.

It is one strategy in N markets, **not** N strategies: building the owner's real portfolio is
`portfolio/`, where `DECISIONS.md` still has the design open.

## The cost stress stopped using round numbers

`execution.yaml` holds, per feed, a typical and a stressed spread in points, a commission in USD per
lot per side, a typical slippage and the tick size. `stress.cost_shock` is now `spread_stress /
spread_typical` and `stress.fill_depth` is two sides of that slippage as a fraction of the median
MAE, both per market, instead of `[1.0, 2.0]` and `0.25` — numbers nobody had chosen. `p_skip` is
**not** calibrated and is labelled as the assumption it is: nothing in the export says how often an
order would have been missed.

⚠️ **The values in `execution.yaml` are placeholders** written as a typical CFD broker's, so the
owner has something concrete to correct; each block carries `source: placeholder` and
`reviewed_by_owner: false`, and the panel prints both. They are deliberately **not** in
`assets/*.yaml`: those files gate every project in this repo through `core.assets`, and
`assets/RULES.md` says a file with invented values is worse than no file, because it looks decided.
A feed that does have an asset file reads its decided spread from there instead.

The tab also prints, per market, the cost SQX **really charged** — recovered per trade from its own
P/L, and the truth — against what `execution.yaml` implies, and flags a gap past 25%. Measured today
on Brent: 25.85 charged against 37.46 modelled, +45%, which is the placeholder being wrong and the
table doing its job.

## A warning now says what it does not affect

Each of the seven is four fields instead of one sentence: what fired it **with the number that
fired it**, what it affects, what it does *not*, and what to do. The missing half was the third one.
`bad_hold_fit` touches exactly one null model — the other three reuse the real holds and are immune.
`no_drift` touches exactly one number — A and A per unit of risk are unaffected, and Brent, which
fires it, has the strongest A of the three. `pending_fills` touches Test 1a only; 1b and 1c use no
null model at all. Read as one sentence, all three looked like they invalidated the market.

## The panel reports more trades than the tests use, on purpose

🔬 Found 2026-09-16 by the owner, comparing `Strategy 24.7.38` against SQX: the panel showed 2,089
trades on gold where the databank had 2,142. `envelope.occupancy()` keeps a trade only when
`exit > entry`, and **1,695 of the databank's 92,329 trades open and close inside one bar** —
zero-duration `Exit Signal` exits, `Time in trade` of `0s`. Five more fall before the first bar of
their file. 1.84% overall; 9.8% on the worst pair, `Strategy 8.16.41(1)` on silver.

Dropping them from the **tests** is right and stays: a trade with no interval cannot be displaced by
a null model, has no blind window of its own duration to be matched against, and occupies no bars to
count as exposure. Dropping them from the **reported backtest** was a defect — their P&L is real,
so net profit, drawdown, profit factor and the trade count were all quietly short of what SQX said.

Both are now computed and both are shown:

| what | from | used by |
|---|---|---|
| `realrun.reported()` | **every** trade SQX reported, in close-time order | the master table, the equal-risk table, the equity curves, the portfolio |
| `realrun.real()` | the trades the bar grid can hold | the null comparison, where the real run and its random counterparts must be the same trades |

🔬 Verified on `Strategy 24.7.38`: the panel's net now equals the sum of the export's own
`Profit/Loss` column to the cent on all three markets. The master table prints both counts, a note
under it says why they differ, and `diagnostics.min_on_grid` (0.95) raises the new `off_grid`
warning when the gap is large enough to change how a p-value should be read.

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

Write a function in `trade_models.py` — or in `free_models.py` if it re-lays the whole run — with
the shared signature, `(held, market, draws, rng, batch)` in and `(entries, holds)` out; add it to
`MODELS`, and add a row to `RANDOMISES` saying **what it randomises**. `batch` is how many draws
were already produced, and only a model whose randomness must match across markets needs it:
`block_shift` keys its displacement on the calendar rather than on `rng`, and without `batch` every
chunk of the batched loop would redraw the same one. Nothing else changes: the drawer picks it up and the test explorer gains an entry.

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
to; the drift and the correlation describe the wrong stretch; and the equity axis spans years
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

### `block_shift` overlapped its own trades until 2026-09-17, and it is the headline model

🔬 Measured 2026-09-17 on `Strategy 24.14.35`, 500 draws, both OOS markets: **5.38% of Brent's
random trades and 2.82% of silver's open before an earlier trade of the same run has closed**, under
`block_shift`. The three free models read 0.0000% on the same pairs — `_lay` fixed them, and
`regime_strata` drops its clashes in `_drop_overlaps`, but `block_shift` has never been checked. It
moves each block's trades by whole weeks *inside the weekday-hour index*, which is not a rigid
translation in bar space, so a hold that was legal at its real position can reach into the next
trade at the new one. The strategy is single-position, so those runs are holding two at once.

What it costs, measured at 5,000 draws against the same model with `_drop_overlaps` applied:
p(`mean_r`) 0.0038 → 0.0044 on Brent and 0.0278 → 0.0288 on silver; p(`net`) 0.0048 → 0.0036 and
0.0610 → 0.0628; σ of net **5% narrower** without the clashes; live trades 782 → 740 and 844 → 820.
So the direction is not even consistent and the size is thousandths — this is a correctness defect
worth naming, not a result that changes.

**Repaired 2026-09-17 by cutting, not by dropping.** `trade_models.cut_at_next()` caps every hold
at the bar the next trade opens, exactly as the Friday close already caps one. That keeps the trade
count — dropping the clashing trade removed 3-5% of every run and traded an exposure bias for a
sample-size one — and re-measured afterwards the overlap is **0.0000%** on both markets under all
four models. `tests/test_models.py` now holds the property.

🔬 **`block_shift` still overlaps**: 2.5% of trades on XAGUSD and 1.7% on Brent (Strategy 1.10.80),
because trades in different weekday-hour groups wrap by different numbers of weeks. It was left as it
is on purpose — the owner fixed it as the reference the window sweep is read against — and is recorded
here rather than changed.

## Does it generalise? The joint null

Built 2026-09-17. The per-market tests ask whether the timing carried information *on that market*;
the retest exists to ask whether it carries **across** markets, and counting how many markets came
in under alpha does not answer that. Those p-values are dependent — same draws, markets that move
together — so a vote, a Fisher combination or a Stouffer one is anti-conservative exactly where it
matters.

`joint.py` computes **one a-priori statistic and one p**: the equal-weight mean of `mean_r` over the
out-of-sample markets, against the same pooled mean on every draw. Equal weight because each market
is one vote that the edge generalises; weighting by trade count lets the busiest market decide alone.
The base asset is not in the pool — there a strategy beats its null by construction, so including it
would import a guaranteed pass. 🔬 Measured on `Strategy 24.14.35` at 3,000 draws over Brent and
silver: pooled real `mean_r` **+0.1757** against a null median of −0.0860, **p = 0.0010**, z = +3.36.

**What makes it correctly sized is the coupling, not the pooling.** 🔬 Until 2026-09-17 the draws
were independent across markets — measured, the correlation between draw *d*'s `mean_r` on Brent and
on silver was **−0.0016** — because sharing `nulls.seed` couples nothing: every market builds its own
generator and consumes it at its own shape. `trade_models.semester_shift()` now draws the
displacement of each **calendar semester** from a generator keyed by that semester, so draw *d*
moves 2013H1 the same way everywhere. `envelope.periods()` is what gives a semester an identity
independent of when a market's data starts. Measured after the change, 83.5% of draws displace a
shared semester by exactly the same number of weeks in both markets; the rest differ only where the
wrap folds a weekday-hour group of a different length.

🔬 And the honest part: the per-draw correlation between the two markets' `mean_r` is still about
**−0.035** even coupled. These two markets' null statistics simply do not co-move much at the
horizon of these trades. That is not a reason to skip the joint null — its whole point is to be
correctly sized *whatever* the correlation turns out to be, and with four markets planned it will
not stay near zero — but it does mean the joint p here is close to what independence would have
given, and saying otherwise would be selling it.

`joint.pool` chooses the scale. The default `mean_r` averages the raw statistic and is right while
the markets' null spreads sit within a small factor of each other — 🔬 measured 0.1236 against
0.1026, a factor of 1.20. Switch it to `z` when one market's spread is several times another's, or
that market decides the verdict on scale alone.

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
- **Every point is a full null, and every statistic is swept.** Each sweep point goes through the
  same `backtest.drawn()` + `backtest.summary()` as a null model, so it keeps the whole metric table,
  a histogram per metric and an equity cone. The panel's statistic dropdown then reads the sweep in
  Net profit, Return/DD, drawdown, Sharpe or PF, not only in `mean_r`, and the trend caption is
  computed per statistic. Until 2026-09-16 a sweep point priced `mean_r` and the trade count alone.
- **It costs time**: nine more nulls per market, now at full price. 🔬 Measured on Strategy 24.14.35
  over two markets at the default 25,000 draws: **107 s**, against 36-52 s when the sweep priced one
  statistic, and about 25 s before there was a sweep at all. 🔬 After the 2026-09-16 rebuild,
  Strategy 2.29.29 over the same two markets is **95 s** — the sweep is still most of it, and what
  the rebuild added on top is the cost stress drawing 25,000 runs instead of 5,000, Test 1b running
  under four reference windows, and the portfolio account.

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
than sampled: the mean of *every* window of that length near the trade, not a sample of them.
The source note's literal version — each trade against a passive long over the identical window — is
degenerate for this family: these strategies carry no stop and no target, so their trade return *is*
that passive long, and the difference would be zero by construction.

### What "near the trade" means, and why it is now swept

The reference used to be the **fixed semester partition** `block_shift` moves trades inside. That
partition has a defect nobody had written down: a trade entering three days before a block ends is
measured against a stretch that is almost entirely past, and two trades a week apart across a
boundary get *disjoint* references. `paired.reference` now defaults to a **centered window** —
every blind trade of the same length starting within `±3 months` of the entry, by running mean, one
pass per distinct hold. It reads bars after the entry as well as before, which is fine: the
reference is "what this market was paying around then", not a rule anyone could have traded.

Because the choice is a modelling decision and not a fact, **the test is run under all of
`paired.sensitivity` and the panel prints every one**: ±3m, ±6m, ±12m and the block partition. A
p-value that survives four definitions does not depend on the definition; one that survives a single
one was being carried by it. 🔬 Measured on `Strategy 1.10.80`, Brent: p 0.749 / 0.677 / 0.667 /
0.753 and alpha −5.3 / −4.7 / −4.7 / −5.2 bps across the four — the choice moves nothing on that
pair, which is the outcome to hope for and not the one to assume.

**The alpha is reported in five units.** 0.00042 is unreadable, so `units.py` prints the same number
in basis points, in per cent, in ATR units, in dollars per trade and — the one to read first — in
**dollars accumulated over the whole sample**: how much of the money the strategy made was put there
by *when* it entered rather than by being in the market at all.

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
- **E is never a bare number.** It divides by the market's own drift, so where that drift is not
  distinguishable from zero the ratio has no finite interval at all. It is now always shown with a
  **Fieller interval**, which returns the unbounded one and says so, beside the share of bootstrap
  replicates whose denominator changed sign. Measured on Brent: E = +17.4, CI *no acotado*, 54.5% of
  replicates with a drift at or below zero. The number the panel leads with is **A per unit of
  risk**, which divides by the market's typical bar move and is therefore defined everywhere.
- **A confidence interval brackets the estimator it is an interval for.** A's bootstrap is weighted by
  holds because A itself is pooled over occupied bars; unweighted, it sat 9% away from its own point
  estimate.
- **Long only.** `pricing.require_long_only()` refuses anything else rather than silently flipping a
  sign. Checked: all 92,329 trades of the 30-strategy sample are Buy.
- **Read the luck figure before any p-value.** It is a scale for reading a table, not a rule.
