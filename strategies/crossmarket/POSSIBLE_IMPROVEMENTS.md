# Possible improvements — cross-market analysis

Ideas that were considered and deliberately left out of the first build, so that the reason for
leaving them out does not have to be rediscovered. Nothing here is a bug. Ordered by how much it
would change a conclusion.

## 1. How the null models the real trades — the open end of the whole test

**This is the largest source of arbitrariness in the test.** There is no single correct way to turn a
real run into a random one, and the answer moves with the choice. That is why `model/trade_models.py` is a
registry rather than one function: four models ship, they share a signature, and each declares in
`RANDOMISES` what it changes. Adding a fifth is a function and a row.

What ships (2026-09-15): `segment_permute` "Shuffled Sequence", `resampled_holds` "Resampled
Sequence", `fitted_holds` "Fitted Distributions Sequence" — the three that re-lay the run anywhere
in the backtest window — and `block_shift` "Calendar Shift", which moves each trade inside its own
regime block and weekday-hour slot and is the one `nulls.headline` names. A fifth, `renewal`, was
built and then **retired the same day**: measured over 8 (strategy, market) pairs it matched
`resampled_holds` to within 2% on null width and 0.004 on p. Do not add it back without a
measurement that says it separates.

**Built 2026-09-14, and the reason it matters.** Every model now re-cuts its holds at the Friday
close (`trade_models.truncate`), because these strategies carry an "End Of Friday (Time)" exit — 5.4%
of the 92,329 trades in the 30-strategy sample. Without it a random trade laid down on a Friday
afternoon held through a weekend the real one never held. `Exit Signal` (16.6%) is the part that
still cannot be reproduced without reading the `.sqx`, and it is why those strategies are reported
as a joint entry-and-exit test.

Still worth building:

- **A joint null across markets.** ✅ *Built 2026-09-17* — `simulate/joint.py`, and `block_shift` now draws
  one displacement per calendar semester and applies it in every market, which is what makes the
  pooled p correctly sized. What is left is the scale question in §6 of the brief it came from:
  `joint.pool` defaults to raw `mean_r` and should be revisited when a market arrives whose null
  spread is several times another's.
- **Condition the model on state.** *Partly built 2026-09-15:* `regime_strata` conditions on ATR
  quantile × trend sign and is off by default, and the window sweep conditions the three free
  models on calendar proximity. Draw entries only from bars in the same volatility decile, the
  same trend regime, or the same session as the real entries. Every condition added removes one
  explanation the strategy could be given credit for — deciding which of them the strategy is
  *allowed* to be rewarded for is a modelling choice, not a technical one, and it should be made and
  written down before the numbers are looked at.
- **Richer fits.** `_fit` picks a negative binomial or a Poisson by dispersion alone. A mixture, or a
  fit to the log-duration, would describe a two-population strategy (bar cap plus signal exit) that
  neither of those two can. `goodness()` is what says whether it is needed.
- **Randomise the size, not only the time.** The statistic is size-free today. A model that also drew
  position sizes would let the test say something about the equity curve, which it currently cannot.
- **Vary the number of trades.** Every shipped model fixes N at the real count. One that resampled N
  would fold trade frequency into the comparison instead of holding it constant.

Whatever is added, the rule stays: **a model that changes more than one thing cannot attribute a low
p-value to any single cause.** It can still be worth running — it answers a different question — but
the verdict stays with the model that changes exactly one, and the difference between them is
reported rather than averaged away.

## 2. Statistical treatment

- **Joint null across markets.** ✅ *Built 2026-09-17.* `simulate/joint.run()` pools the out-of-sample
  markets into one a-priori statistic — the equal-weight mean of `mean_r` — and compares it against
  the same pool on every draw. It is correctly sized because the draws are **coupled**:
  `model/trade_models.semester_shift()` keys each calendar semester's displacement on the semester itself
  rather than on the market, so draw d is one counterfactual of the whole set.

  🔬 The measurement that forced this: before the coupling existed, the correlation between draw d's
  `mean_r` on Brent and on silver was **−0.0016**. Sharing `nulls.seed` couples nothing — every
  market consumes its own generator at its own shape. After it, 83.5% of draws move a shared
  semester by exactly the same number of weeks. The per-draw correlation of the two markets'
  statistics is still ≈ −0.035, which is a fact about these two markets and not about the method.
  `diagnostics.correlated`, the assumed-correlation knob kept for an "honest false-pass figure",
  was **removed the same day**: nothing read it, and a measured joint p is what it was standing in
  for.
- **Combine p-values (Fisher / Stouffer)** rather than voting. Rejected, and it should stay
  rejected: both assume independence, which the per-market p-values do not have — same draws,
  markets that move together. The joint null above needs no such assumption, which is the whole
  reason it is the one that ships.
- **Two-stage refinement.** The default 25,000 draws bound the smallest p at 4e-5; across hundreds
  of strategies no FDR procedure can then reach a low q. Screen low, then re-run only the survivors
  high — the panel's per-market **run** button already does exactly that without recomputing the
  other markets.
- **Exact shift null by FFT.** For the fixed-bar-cap family every trade's payoff is a pure function
  of its entry bar, so the whole global-shift null is one cross-correlation of the occupancy vector
  with the payoff vector — every shift at once, no sampling error, in milliseconds. It was written
  and then removed because the shift that matters is stratified by regime block and does not reduce
  to a single circular correlation. Worth revisiting for the per-block correlations.
- **Minimum track-record length per market.** Built in `verdict/significance.min_track_record()` —
  Bailey/López de Prado, on the real per-trade returns. It is a diagnostic that raises the
  `short_sample` warning; nothing is excluded by it. Its kurtosis term took **raw** kurtosis, not
  excess, and was passing excess: fixed 2026-09-14. On this data the correction is small (118.9 →
  120.9 trades needed on gold) because the per-trade Sharpe is small, but it grows with Sharpe².
- **Deduplicate on the trade list** before counting how many strategies passed: 45 of 231 strategies
  once shared byte-identical trades under different names, so a raw count of survivors is inflated.

## What changed on 2026-09-14, and why

The owner's instruction was: no verdict, a tool that produces the data and the analysis. That
removed a whole layer and fixed several things that the verdict layer had been hiding.

- **The verdict is gone.** `verdict/inference.call()`, `verdict/inference.table()`, MANTENER/DESCARTAR/NO EVALUABLE,
  `MIN_MARKETS` and the majority rule: all removed. `verdict/inference.warnings()` replaces the gate — it
  names every reason to distrust a market and drops none. The old gate was not merely conservative,
  it was structurally broken here: `MIN_MARKETS = 4` against two available markets made NO EVALUABLE
  the only reachable verdict for XAUUSD, regardless of any p-value.
- **E was being reported where it means nothing.** `E = mean(held bars) / mu_m` divides by the
  market's own drift. Measured: gold t = +3.13, silver t = +1.61, Brent t = −0.11. On Brent that
  produced **E = −69.4** for the market with the *strongest* A of the three. E is now withheld
  unless the drift clears `exposure.mu_min_t`, and A — which subtracts instead of dividing — is what
  the panel charts.
- **A's confidence interval was an interval for a different estimator.** The point estimate pooled
  every occupied bar; the bootstrap took an unweighted mean of per-trade means. 4.60e-5 against
  5.00e-5 on gold, a 9% gap. The bootstrap is now weighted by holds.
- **The panel declared its own results stale.** Its GET routes read the start-up config while its
  POST routes honoured the drawer, so any override made every stored result permanently red.
  `explorer/scope.from_query()` and `overrideQS()` fix it, copying `monteCarlo/explorer`.
- **`simulate/backtest.setting()` ran six times per market** — once per model inside `run()`, again in
  `analyse_market`, again inside `exposure.run` — each doing a reconcile and a least-squares fit. It
  now runs once and is passed in.
- **Shorts were priced as longs.** Every return is `log(exit/entry)`; a short would have come out
  with the sign reversed and nothing would have noticed. `mechanics/pricing.require_long_only()` refuses
  instead. All 92,329 trades of the sample are Buy, so this is an assertion about the data, not a
  case to handle — short support is a modelling decision (the null's drift exposure changes with
  it), not a sign flip.
- **A strategy with no trades on a market used to crash the run.** The export writes a market's file
  only when the strategy traded there; 2 of 30 sampled strategies never fired on silver. That market
  is now recorded as absent for that strategy and reported, rather than read as a missing input.

## What was built from the source note on 2026-09-14

- **Test 1b (PDF §3), in the only form that says anything here.** The note's literal version — each
  trade against a passive long over the identical window — is **degenerate for this family**: these
  strategies carry no stop and no target, so under the reconciled open-to-open convention the trade
  return *is* that passive long and every difference would be exactly zero. What `simulate/paired.py` builds
  instead is each trade against the **exact mean of every window of its own length inside its own
  regime block**. Exact rather than sampled, paired, Wilcoxon-tested, and — because cost appears on
  both sides and cancels — the one test here that needs neither a null model nor a cost assumption.
  Measured on four strategies: p between 1e-5 and 6e-3 on gold (the fitted market, as expected),
  mostly not significant on silver, mixed on Brent.
- **The market drivers (PDF §5.4), as metrics.** `drivers.py` computes Hurst, the Lo-MacKinlay
  variance ratio, the ADX trend share, ATR% and the Kaufman efficiency ratio per market. Measured:
  gold Hurst 0.500 / VR 0.966, silver 0.478 / 0.738, Brent 0.495 / 0.982. **The regression is not
  built and should not be**: it needs six or more markets on the right-hand side and there are two.
  When `structure` is populated, the metrics are already there.
- **Every knob in one file.** `config.yaml` holds all 25, `inputs/config.py` reads it, `explorer/tooltips.py` gives
  each one a sentence, and the panel's drawer groups them. Nothing is hidden in a module constant
  any more.

## Why two PDF sections are still deliberately left out

Decided with the owner, so a future session does not reopen them alone:

- **Deflated Sharpe Ratio (PDF §5.1).** Not built. DSR needs the number of trials the generation
  search actually made; this project has no such count (see the same reasoning in
  `strategies/monteCarlo/README.md`), and fabricating one would produce a number that looks rigorous
  and is not. `verdict/significance.min_track_record()` covers the part of §5.1 that does not need a trial
  count.
- **The edge-driver regression itself (PDF §5.4).** The indicators are built; the regression is not,
  and cannot be honestly fitted on two markets. It is waiting for the `structure` category.
- **Any combined score across the tests.** There is no composite, no tier and no verdict. Each test
  is reported as its own number with its own warnings, and the owner weighs them by hand. This is
  the explicit instruction, not an omission.

## What changed on 2026-09-16, and what it closed

The owner rebuilt the panel around the backtest rather than around the tests. Alongside that:

- **Test 1b's reference window is no longer a hidden constant.** It was the fixed semester
  partition; it is now a **centered window** by default (`paired.reference: 3`, meaning ±3 months)
  and the test is run under every entry of `paired.sensitivity` — ±3m, ±6m, ±12m and the block
  partition — with all four printed. The block partition's defect is real and had never been
  written down: a trade entering three days before a block ends is measured against a stretch that
  is almost entirely past, and two trades a week apart across a boundary get disjoint references.
  Measured on `Strategy 1.10.80` / Brent the four agree to within 0.09 on p; that is a measurement,
  not a reason to stop printing them.
- **E has an interval.** `verdict/fieller.py` gives the ratio an honest one: unbounded when the denominator
  cannot be told from zero, which is the truth a percentile bootstrap quietly hides. The bootstrap
  behind it resamples **blocks of bars** and computes numerator and denominator from the same
  replicate, so the dependence between the occupied bars and the market they are a subset of is
  carried rather than assumed away; the share of replicates whose drift changed sign is printed
  beside it. Brent: E = +17.4, unbounded, 54.5% sign flips.
- **The fingerprint draws its distributions.** Closes §6 below: `simulate/fingerprint.overlay()` returns
  shared bins and two share arrays, and the tab lays this market's holds, returns, MAE/ATR and
  MFE/ATR over the base asset's.
- **The cost stress is calibrated per feed** from `execution.yaml` instead of round numbers, and
  the tab prints the cost SQX really charged against the one that file implies. `p_skip` stays an
  assumption and is labelled as one.
- **Warnings say what they do not affect.** See `verdict/alerts.py`.
- **The Portfolio tab** answers the question the retest raises and could not: does a market break the
  combination? Marginal contribution per market, calendar-block intervals, overlap, and reordering
  delegated to `engines.resample.draws`.

### Discarded on 2026-09-16, with the reason, so they are not proposed again

- **The edge-driver regression, and `drivers.py` with it.** It needs six or more markets on the
  right-hand side. The owner expects four, and says they will be uncorrelated — which helps the
  regression not at all, since the constraint is the count. Hurst, VR, ADX share, ATR% and the
  efficiency ratio are gone from the code; if six markets ever exist, they are forty lines to
  rebuild and the argument for them is in this file's history.
- **The PCA across market equity streams.** With two or three streams PC1 is close to a function of
  the mean pairwise correlation, so it was a second name for a number the matrix already showed.
  The correlation matrix survives and moved onto the main tab, where it sits under the equity
  curves it describes.

## What was built on 2026-09-21: the main backtest's own OOS stretch

The owner asked for the same random-entry test over the segment of the **main** backtest that the
builder optimised nothing on — an OOS of time, next to the retest's OOS of market. It runs in
`orchestrate/stretch.py`, lands in `record["oos"]` and nowhere else, and has its own tab.

Decided with the owner, so a future session does not reopen them:

- **The OOS stretch only, not the IS beside it.** The IS contrast was offered and declined. It is
  cheap to add — the same call on the complementary slice — and it is what makes the OOS p readable:
  351 trades give a wider null and a higher p by sample size alone, and without the IS number there
  is nothing to separate "the window is short" from "the edge is gone". If the OOS p ever looks
  ambiguous, that is the first thing to build.
- **It is not evidence alongside the additional markets.** Not in the joint null, not in the breadth
  count, not in the portfolio or the correlation matrix. Gold-2018 is the same market as gold, over
  dates that overlap silver's and Brent's, and `joint.py` is sized for markets displaced together by
  `semester_shift`. Pooling it there would be wrong in a way no output would show.
- **No window sweep on it.** Five years in 3-year / 1-year / 6-month blocks leaves every block under
  `sweep.min_trades`; every point would be withheld.

🔬 **The measurement that came out of building it, and it is not about the OOS.** `fill_mismatch`
fires on every gold window — the base asset's own row had never been warning-checked, so nobody had
seen it. The cause is the feed, not the study: gold M30 records the Buy entry 0.05–0.06 above the bar
open (the entry-side spread) while silver and Brent record 0 exactly. The convention is still
open-to-open and the study is still priced consistently, because `charged` recovers that 0.05 per
trade and every random run pays it too. `knowhow/export/fill-and-pricing.md` holds the arithmetic.

What that leaves open, for the owner to decide rather than for a session to retune quietly:
`diagnostics` has no tolerance for the fill error — `fill_mismatch` fires on `> 0`, full stop — so on
this feed it is permanently on, and `verdict/alerts.py` tells the reader "éste sí es grave" about a
constant half-spread. Either the check gets a tolerance in price units, or the warning's text learns
to separate a spread from a wrong convention. Both change what every market reports, which is why
neither was done here.

- **The only strictly unseen window starts 2023-01-01.** Every `dateTo` in the project stops at
  2022.12.31 while the bar files run to 2026. A retest from there would be out of sample for the base
  asset and for the additional markets at once, and it would need no `selected_window` warning. It is
  the retest worth asking SQX for; it is in `OPEN.md`, not here, because it is data and not code.

## 3. Other tests on the same two inputs

- **Test 1c, exposure-adjusted return.** Concentration ratio E and drift-neutral excess A. Cheaper
  than this test and answers a different question: beating the market's own average bar rather than
  beating chance. Built in `simulate/exposure.py`. Sanity check against `trade_models.block_shift`-style
  random entries on `XAGUSD_DukasM1_Infinox` gives E ≈ 1.13, A ≈ 1.5e-6 — near 1 and 0 as the PDF
  predicts. The real strategy there (913 trades) measures E ≈ 3.28, A ≈ 2.5e-5 (CI 90%
  [-2.9e-5, 7.3e-5] — the lower bound crosses zero on this one strategy), risk-normalised A ≈ 0.006.
  **`capture_ratio` used to come out ±inf**: 7 of 844 trades on that market have MFE = 0 (the trade
  never moved favourably at all), which divided by zero. Those trades are now excluded and counted
  (`exposure.drop_zero_mfe`, on by default), because a trade that never moved favourably has an
  undefined capture, not an infinite one. The count of dropped trades is reported beside the ratio.
- **Cost gradient** 1x to 3x with the breakeven multiple per market.
- **Per-market equity curves without SQX.** A retested `.sqx` already stores one `dailyEquity.bin`
  per `AdditionalMarket` result; teaching `core/sqxstats.equity()` to read a named result would give
  a free cross-check of every market's P/L and the input to the independence test, with no export.

## 4. Fills: ✅ the two checks now measure what they claimed to

**Fixed 2026-09-21.** Both warnings were reading the wrong quantity and firing on data with nothing
wrong with it. `mechanics/pricing.fill_profile()` replaces both readings:

| | read before | reads now |
|---|---|---|
| `pending_fills` | the entry **clock** — is the timestamp a bar boundary | the entry **price** against its own bar's, discounting the market's constant spread |
| `fill_mismatch` | `fill_error > 0` | median error above `diagnostics.max_fill_error`, in median-ATR units |

🔬 **Why the clock was wrong.** Over `raw/XAUUSD/MC_Trades/2026-09-19` — 757 strategies, 960,705
trades — the 4,613 entries stamped inside a bar are priced *identically* to the 956,092 stamped on
it: both at exactly bar open + 0.08/0.09, and not one of the 4,613 outside `[0, 0.10]`. On gold's
retest export the late entries land only on minute 1 and 31. They are stamping artefacts. Silver at
92.1% and Brent at 92.0% were reporting nothing, and the Brent result at p = 0.005 that the
2026-09-14 note mourns was gated on something that was never happening.

🔬 **Why `> 0` was wrong.** A constant offset is a **spread**. `backtest.setting()` recovers
`charged = gross(bar opens) − reported P/L`, which works out to `spread × Size + commission`, so the
spread lands inside the per-trade cost every random run also pays; and `mean_r` is bar-open to
bar-open on both sides and never sees it. Real and null are on the same pricer either way. What a
wrong feed or a wrong timeframe produces is a *large* or *dispersed* error, and that is what the
check now asks about.

**The thresholds, and the measurement behind each.** `fill_tolerance: 0.05` ATR — the maximum
deviation from the constant offset measured over 28,490 trades is **0.0045 ATR**, one tick, so the
tolerance has an order of magnitude of headroom. `max_fill_error: 0.25` ATR — gold's spread, the
largest legitimate offset on this install, is **0.023 ATR**; a wrong feed is of the order of a whole
bar range.

**Both were verified to still fire**, because a check that cannot fire is worthless: a feed displaced
3 ATR trips `fill_mismatch` (3.000 ATR); 6% of entries moved half an ATR off their bar trips
`pending_fills` (0.948) while 3% does not (0.975); and H1 bars under an M30 backtest drop
`on_open_price` to **0.566** without touching `fill_error`, because half the H1 opens coincide with
an M30 open — which is why the two checks are kept as a pair and why `pending_fills`' advice now
names the timeframe.

### Still worth building, for a fleet that has stops

🔬 **This fleet has none.** Across the same 757 strategies the only `Close type` values are
`Exit After X Bars` (720,874), `Exit Signal` (187,853) and `End Of Friday (Time)` (51,978) — zero
`Stop Loss`, zero `Take Profit`, zero trailing — and every exit price is its bar's open, median
error 0.0000 with a **maximum of 0.0100** across all 757. Nothing happens inside a bar here. The
three ideas below are for the day that stops being true, and
`pricing.fill_profile()["error"]` on the exit side is the instrument that will say when it does.

- **M1 execution.** Asked by the owner 2026-09-21 and measured then: it fixes nothing for this fleet
  and would make the pricing *worse*, because SQX executed on the logic timeframe's bar opens and
  pricing on M1 would put the study on a grid SQX never used. The zero-duration trades share one
  timestamp, so no resolution recovers an interval; the late entries are at their bar's open price;
  and the 0.05–0.09 offset is a spread, which no timeframe changes. It becomes the right build once
  exits stop landing on bar opens, and then its shape matters: **entries drawn on the logic
  timeframe's grid** — an M1 placement grid hands the null 30× more room and makes it a different,
  wider null whose p moved for reasons that have nothing to do with the strategy — **holds carried in
  minutes**, and only the pricing on M1. Even then it makes the *pricing* honest, not the
  *selection*: a limit fill is still a price-conditional event a displaced trade cannot reproduce.
- **Model the fill.** Give a random trade the same limit or stop offset the real one used and walk the
  bar's OHLC to see whether it would have filled. That reproduces the mechanism instead of excluding
  it, and needs the strategy's order type, which is in the `.sqx`. This is the real answer, and M1
  execution is what would make it precise.
- **Test the reproducible subset.** Keep only the trades that took their bar's price, and say so: the
  result is then about that share of the strategy, which is a weaker claim but a real one. It needs
  care — dropping them is itself a selection, and the kept subset may be systematically easier.
- **Grade the evidence.** Attach a confidence weight to the market rather than a sentence, so a
  market at 92% is visibly worth less than one at 100% when several are read together.

## 5. Known confounders left declared rather than fixed

- **Swap.** An eight-bar H1 hold often crosses the rollover, and how many rollovers a trade takes
  depends on its entry hour. The shift null preserves the entry hour, so this is controlled; the
  permutation null does not, which is one more reason it is only a robustness check.
- **Pending orders.** A limit or stop fill is a price-conditional selection the null cannot
  reproduce. Markets where fewer than 95% of entries land on a bar open are dropped from the vote
  rather than corrected.
- **Risk-based sizing.** The statistic is size-free, which makes it exchangeable but also means a
  passing p-value says nothing about the equity curve.

## 6. Left out of the Fase 1-4 + panel build

- ~~No holding-time comparison chart.~~ **Built 2026-09-16.** `simulate/fingerprint.overlay()` bins this
  market and the base asset on shared edges, as shares rather than counts so different trade counts
  compare, clipped at the 99th percentile of the two together — one 400-bar hold otherwise squeezed
  900 trades into a single bar. Four of them: holds, returns, MAE/ATR, MFE/ATR. The drawing lives in
  `render/overlays.py`, not `render/charts.py`, which was already at the line cap.
- **Manual screenshots are placeholders.** `docs/manual/05-retest-mercados.md` describes every button
  and tab from a real run of the panel (verified against `Retest_Markets_-_Family`'s one strategy,
  which reproduces the known `Strategy 24.14.35` pending-order case in §4 above byte-for-byte), but
  carries no screenshots yet — this session has no browser to capture them from, and rule 8 forbids
  inventing them. Whoever next opens the panel for real should paste a few in.
