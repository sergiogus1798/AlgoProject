# Possible improvements — cross-market analysis

Ideas that were considered and deliberately left out of the first build, so that the reason for
leaving them out does not have to be rediscovered. Nothing here is a bug. Ordered by how much it
would change a conclusion.

## 1. How the null models the real trades — the open end of the whole test

**This is the largest source of arbitrariness in the test.** There is no single correct way to turn a
real run into a random one, and the answer moves with the choice. That is why `trade_models.py` is a
registry rather than one function: four models ship, they share a signature, and each declares in
`RANDOMISES` what it changes. Adding a fifth is a function and a row.

What ships: `block_shift` (placement only — the verdict), `segment_permute` (placement, order,
clustering), `resampled_holds` (which holds and gaps occur), `fitted_holds` (a negative binomial or
Poisson fitted to the real holds and gaps).

Still worth building:

- **Renewal null (Null A of the source note).** Walk the bars, and when flat decide to enter with the
  empirical hazard, hold, force flat, repeat. Rebuilds the occupancy from scratch rather than moving
  an existing one; the trade count is then random too, which is more honest about sample size and
  harder to compare.
- **Condition the model on state.** Draw entries only from bars in the same volatility decile, the
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
- **Two-stage refinement.** 5,000 draws bound the smallest p at 2e-4; across hundreds of strategies
  no FDR procedure can then reach a low q. Screen at 5,000 draws, then re-run only the survivors at
  200,000.
- **Exact shift null by FFT.** For the fixed-bar-cap family every trade's payoff is a pure function
  of its entry bar, so the whole global-shift null is one cross-correlation of the occupancy vector
  with the payoff vector — every shift at once, no sampling error, in milliseconds. It was written
  and then removed because the shift that matters is stratified by regime block and does not reduce
  to a single circular correlation. Worth revisiting for the per-block correlations.
- **Minimum track-record length per market** instead of the flat 30-trade floor. Built in
  `significance.min_track_record()` — Bailey/López de Prado, on the real per-trade returns. It is a
  diagnostic beside `inference.testable()`, not a replacement for it: the owner decided the verdict
  stays with `inference.call()` on `block_shift` alone (see the note below on why nothing here feeds
  back into it).
- **Deduplicate on the trade list** before counting how many strategies passed: 45 of 231 strategies
  once shared byte-identical trades under different names, so a raw count of survivors is inflated.

## Why three PDF sections were deliberately left out

Decided with the owner before this build started, so a future session does not reopen them alone:

- **Deflated Sharpe Ratio (PDF §5.1).** Not built. DSR needs the number of trials the generation
  search actually made; this project has no such count (see the same reasoning in
  `strategies/monteCarlo/README.md`), and fabricating one would produce a number that looks rigorous
  and is not. `significance.min_track_record()` covers the part of §5.1 that does not need a trial
  count.
- **Edge-driver regression (PDF §5.4), and the loose structural indicators it would need** — Hurst
  exponent, variance ratio, ADX%, ATR%, efficiency ratio. Not built, none of it. The owner's call:
  the regression turns "it works here and not there" into "why", which is valuable, but it is a
  separate, larger study and was kept out of this round entirely.
- **Combined verdict across the new tests.** `inference.call()` on `block_shift` remains the only
  thing that decides MANTENER / DESCARTAR / NO EVALUABLE. Test 1c, significance, breadth, the
  fingerprint, cost robustness and correlation/PCA are each reported as their own diagnostic in the
  panel; the owner reads them and weighs them by hand rather than folding them into one number.

## 3. Other tests on the same two inputs

- **Test 1c, exposure-adjusted return.** Concentration ratio E and drift-neutral excess A. Cheaper
  than this test and answers a different question: beating the market's own average bar rather than
  beating chance. Built in `exposure.py`. Sanity check against `trade_models.block_shift`-style
  random entries on `XAGUSD_DukasM1_Infinox` gives E ≈ 1.13, A ≈ 1.5e-6 — near 1 and 0 as the PDF
  predicts. The real strategy there (913 trades) measures E ≈ 3.28, A ≈ 2.5e-5 (CI 90%
  [-2.9e-5, 7.3e-5] — the lower bound crosses zero on this one strategy), risk-normalised A ≈ 0.006.
  **`capture_ratio` can be ±inf**: 7 of 844 trades on that market have MFE = 0 (the trade never
  moved favourably at all), which divides by zero. The panel reports the median, which is robust to
  this; the mean is not and should not be trusted without filtering those trades first.
- **Edge-driver regression.** Hurst, variance ratio, ADX regime share, ATR%, efficiency ratio per
  market, regressed against the per-market result. Turns "it works here and not there" into a
  sentence about which market property the edge needs.
- **Independence / PCA** across the markets' equity streams. If PC1 explains most of the variance,
  eight markets are one bet and a majority of eight is worth much less than it looks.
- **Cost gradient** 1x to 3x with the breakeven multiple per market.
- **Per-market equity curves without SQX.** A retested `.sqx` already stores one `dailyEquity.bin`
  per `AdditionalMarket` result; teaching `core/sqxstats.equity()` to read a named result would give
  a free cross-check of every market's P/L and the input to the independence test, with no export.

## 4. The pending-order guard is all-or-nothing

Found on the first real run. `Strategy 24.14.35` on `Retest Markets - Family` fills on a bar open 98.3%
of the time on gold but 91.8% on silver and 91.4% on Brent, so **both additional markets were dropped
from the vote entirely** and the strategy came out NO EVALUABLE — despite p = 0.005 on Brent under
every model. Losing 100% of a market's evidence over 8% of its trades is a blunt response.

Options, none yet built:

- **Test the reproducible subset.** Keep only the trades that entered on a bar open, and say so: the
  result is then about 92% of the strategy, which is a weaker claim but a real one. It needs care —
  dropping the pending fills is itself a selection, and the kept subset may be systematically easier.
- **Model the fill.** Give a random trade the same limit or stop offset the real one used and walk the
  bar's OHLC to see whether it would have filled. That reproduces the mechanism instead of excluding
  it, and needs the strategy's order type, which is in the `.sqx`.
- **Grade instead of gate.** Report the market with a confidence weight rather than a boolean, so a
  market at 92% contributes less than one at 100% instead of contributing nothing.

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
