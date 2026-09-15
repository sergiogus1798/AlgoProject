# Possible improvements — cross-market analysis

Ideas that were considered and deliberately left out of the first build, so that the reason for
leaving them out does not have to be rediscovered. Nothing here is a bug. Ordered by how much it
would change a conclusion.

## 1. How the null models the real trades — the open end of the whole test

**This is the largest source of arbitrariness in the test.** There is no single correct way to turn a
real run into a random one, and the answer moves with the choice. That is why `trade_models.py` is a
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

- **Joint null across markets.** The seed is already synchronised, so one draw is the same
  displacement in every market. Combining the per-market statistics into one figure per strategy
  under that joint null would price the correlation between markets instead of ignoring it. This is
  the right fix for the false-pass inflation the report currently only declares.
- **Combine p-values (Fisher / Stouffer)** rather than voting. More powerful, but it assumes
  independence, which is precisely what item above measures.
- **Two-stage refinement.** The default 25,000 draws bound the smallest p at 4e-5; across hundreds
  of strategies no FDR procedure can then reach a low q. Screen low, then re-run only the survivors
  high — the panel's per-market **run** button already does exactly that without recomputing the
  other markets.
- **Exact shift null by FFT.** For the fixed-bar-cap family every trade's payoff is a pure function
  of its entry bar, so the whole global-shift null is one cross-correlation of the occupancy vector
  with the payoff vector — every shift at once, no sampling error, in milliseconds. It was written
  and then removed because the shift that matters is stratified by regime block and does not reduce
  to a single circular correlation. Worth revisiting for the per-block correlations.
- **Minimum track-record length per market.** Built in `significance.min_track_record()` —
  Bailey/López de Prado, on the real per-trade returns. It is a diagnostic that raises the
  `short_sample` warning; nothing is excluded by it. Its kurtosis term took **raw** kurtosis, not
  excess, and was passing excess: fixed 2026-09-14. On this data the correction is small (118.9 →
  120.9 trades needed on gold) because the per-trade Sharpe is small, but it grows with Sharpe².
- **Deduplicate on the trade list** before counting how many strategies passed: 45 of 231 strategies
  once shared byte-identical trades under different names, so a raw count of survivors is inflated.

## What changed on 2026-09-14, and why

The owner's instruction was: no verdict, a tool that produces the data and the analysis. That
removed a whole layer and fixed several things that the verdict layer had been hiding.

- **The verdict is gone.** `inference.call()`, `inference.table()`, MANTENER/DESCARTAR/NO EVALUABLE,
  `MIN_MARKETS` and the majority rule: all removed. `inference.warnings()` replaces the gate — it
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
  `scope.from_query()` and `overrideQS()` fix it, copying `monteCarlo/explorer`.
- **`backtest.setting()` ran six times per market** — once per model inside `run()`, again in
  `analyse_market`, again inside `exposure.run` — each doing a reconcile and a least-squares fit. It
  now runs once and is passed in.
- **Shorts were priced as longs.** Every return is `log(exit/entry)`; a short would have come out
  with the sign reversed and nothing would have noticed. `pricing.require_long_only()` refuses
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
  return *is* that passive long and every difference would be exactly zero. What `paired.py` builds
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
- **Every knob in one file.** `config.yaml` holds all 25, `config.py` reads it, `tooltips.py` gives
  each one a sentence, and the panel's drawer groups them. Nothing is hidden in a module constant
  any more.

## Why two PDF sections are still deliberately left out

Decided with the owner, so a future session does not reopen them alone:

- **Deflated Sharpe Ratio (PDF §5.1).** Not built. DSR needs the number of trials the generation
  search actually made; this project has no such count (see the same reasoning in
  `strategies/monteCarlo/README.md`), and fabricating one would produce a number that looks rigorous
  and is not. `significance.min_track_record()` covers the part of §5.1 that does not need a trial
  count.
- **The edge-driver regression itself (PDF §5.4).** The indicators are built; the regression is not,
  and cannot be honestly fitted on two markets. It is waiting for the `structure` category.
- **Any combined score across the tests.** There is no composite, no tier and no verdict. Each test
  is reported as its own number with its own warnings, and the owner weighs them by hand. This is
  the explicit instruction, not an omission.

## 3. Other tests on the same two inputs

- **Test 1c, exposure-adjusted return.** Concentration ratio E and drift-neutral excess A. Cheaper
  than this test and answers a different question: beating the market's own average bar rather than
  beating chance. Built in `exposure.py`. Sanity check against `trade_models.block_shift`-style
  random entries on `XAGUSD_DukasM1_Infinox` gives E ≈ 1.13, A ≈ 1.5e-6 — near 1 and 0 as the PDF
  predicts. The real strategy there (913 trades) measures E ≈ 3.28, A ≈ 2.5e-5 (CI 90%
  [-2.9e-5, 7.3e-5] — the lower bound crosses zero on this one strategy), risk-normalised A ≈ 0.006.
  **`capture_ratio` used to come out ±inf**: 7 of 844 trades on that market have MFE = 0 (the trade
  never moved favourably at all), which divided by zero. Those trades are now excluded and counted
  (`exposure.drop_zero_mfe`, on by default), because a trade that never moved favourably has an
  undefined capture, not an infinite one. The count of dropped trades is reported beside the ratio.
- **Edge-driver regression.** Hurst, variance ratio, ADX regime share, ATR%, efficiency ratio per
  market, regressed against the per-market result. Turns "it works here and not there" into a
  sentence about which market property the edge needs.
- **Independence / PCA** across the markets' equity streams. If PC1 explains most of the variance,
  eight markets are one bet and a majority of eight is worth much less than it looks.
- **Cost gradient** 1x to 3x with the breakeven multiple per market.
- **Per-market equity curves without SQX.** A retested `.sqx` already stores one `dailyEquity.bin`
  per `AdditionalMarket` result; teaching `core/sqxstats.equity()` to read a named result would give
  a free cross-check of every market's P/L and the input to the independence test, with no export.

## 4. Pending orders: the gate is gone, the modelling question is not

The gate that dropped a market over its pending fills is **removed** — `Strategy 24.14.35` fills on a
bar open 98.3% of the time on gold but 91.8% on silver and 91.4% on Brent, and losing 100% of a
market's evidence over 8% of its trades cost a Brent result at p = 0.005 under every model. Those
markets are now reported in full with the `pending_fills` warning.

That fixes the response, not the cause: a limit or stop fill really is a price-conditional selection
the null cannot reproduce, and a market at 91% is genuinely weaker evidence than one at 100%. The
warning says so; it does not quantify it. Still worth building:

- **Test the reproducible subset.** Keep only the trades that entered on a bar open, and say so: the
  result is then about 92% of the strategy, which is a weaker claim but a real one. It needs care —
  dropping the pending fills is itself a selection, and the kept subset may be systematically easier.
- **Model the fill.** Give a random trade the same limit or stop offset the real one used and walk the
  bar's OHLC to see whether it would have filled. That reproduces the mechanism instead of excluding
  it, and needs the strategy's order type, which is in the `.sqx`.
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

- **No holding-time comparison chart.** `fingerprint.holding_ks()` returns only a statistic and a
  p-value, not the two distributions themselves, so the "huella" tab shows a table (`tables.fingerprint_table`)
  rather than the two-histogram overlay the plan sketched. Building it needs `holding_ks()` to also
  return the raw hold arrays (or a second function that does), which was left out to keep `charts.py`
  under CODESTYLE's 250-line cap on this pass.
- **Manual screenshots are placeholders.** `docs/manual/05-retest-mercados.md` describes every button
  and tab from a real run of the panel (verified against `Retest_Markets_-_Family`'s one strategy,
  which reproduces the known `Strategy 24.14.35` pending-order case in §4 above byte-for-byte), but
  carries no screenshots yet — this session has no browser to capture them from, and rule 8 forbids
  inventing them. Whoever next opens the panel for real should paste a few in.
