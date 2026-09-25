# crossmarket/mechanics — what did a trade actually occupy, and what was it worth?

The bar-level machinery the whole study stands on, and the layer `monteCarlo/` has no equivalent of:
where a trade sits on the bar grid, how it is priced from the bars the way SQX priced it, what the
market's regime was at that bar, and what one log return is in money. It answers "what happened",
never "was it luck" — there is no null model here, no draw, no p-value.

**Imports from:** `core/`, and itself
**Consumed by:** `simulate/`, `verdict/`, `render/`, `explorer/`
**Must not contain:** a random draw, a confidence interval, a threshold, or any HTML

| file | what it does | run it | in → out |
|---|---|---|---|
| `pricing.py` | ATR, the cost SQX charged recovered per trade, the net return per trade, the fill convention re-derived by reconciling against SQX's own prices, whether what is left over is a spread or a mismatch, and the long-only assertion | imported | bars + trades → returns, cost, convention, fill profile |
| `envelope.py` | The real run's shape on the bar grid: bars held, gaps, regime blocks, the weekday-hour groups a model may move it to, the bars to each Friday close, and the trades inside one declared stretch of the backtest | imported | trades + bars → the market dict |
| `equity.py` | Equity through the sample on the **calendar**, and the percentile cone around the real curve | imported | P&L + exit bars → curves, bands |
| `curves.py` | Each market's equity on its own real calendar, and what it returned once every market risks the same | imported | fixed → curve, factor |
| `strata.py` | The regime state of every bar — ATR quantile × trend sign — for the optional `regime_strata` model | imported | bars → stratum index |
| `units.py` | One log return in every unit a reader needs: bps, per cent, ATR units, dollars per trade and dollars accumulated | imported | logret → units |

## The window is the backtest's, not the bar file's

🔬 **Every market is sliced to the backtest's own span before anything is computed** —
`envelope.window(trades, bars)`, called once in `orchestrate/strategy.py`. A bar file runs wider than
the retest that was run on it: measured, XAGUSD bars cover 2003-2026 against a 2008-2022 backtest, so
**a third of the file sits outside it**. Without the slice, a null model places trades in years the
real strategy never saw, with their own drift and their own volatility regime; the drift in Test 1c
is measured over the wrong period; Test 1b's blind window averages bars the strategy never had access
to; the drift and the correlation describe the wrong stretch; and the equity axis spans years where
the real curve is flat by construction.

Everything downstream inherits the slice because it is applied to `bars` before `backtest.setting()`.
Each strategy gets its own window, since two strategies in the same databank need not cover the same
period.

## Contracts and traps

- **`pricing.trade_returns()` lives here, not with the statistics that read it.** It is
  `realised(...) − cost`: a measurement. It sat in `verdict/significance.py` until 2026-09-18, which
  made `simulate/fingerprint.py` import the inference layer to get a per-trade return. A module that
  computes the numbers it then judges cannot be cross-examined.
- **Long only.** `pricing.require_long_only()` refuses anything else rather than silently flipping a
  sign. Checked: all 92,329 trades of the 30-strategy sample are Buy.
- **The fill convention is re-derived, never assumed.** `pricing.reconcile()` reproduces SQX's own
  prices per market; `pricing.fill_profile()` then says whether what is left over is a **spread** or a
  **mismatch**, and that distinction is the whole point. Measured: open-to-open everywhere, with a
  median entry error of 0.0000 ATR on silver and Brent and **0.0226 ATR on gold, which is its
  entry-side spread** — a constant every trade pays, absorbed by the per-trade cost `setting()`
  recovers, and therefore paid by every random run too. A *dispersed* error is the one that means
  something, and the maximum deviation from the constant measured over 28,490 trades is 0.0045 ATR:
  one tick. ⚠️ Do not restore a check that demands the error be exactly 0 — it fired on every gold
  window for nothing until 2026-09-21.
- **The cone is drawn on calendar time, not on trade number.** Random runs place their trades at
  different moments, so that is the only axis on which their curves and the real one describe the
  same stretch of market. `equity.path()` bins each trade's P&L into the step its **exit** falls in,
  because that is when the money is realised.
- **`envelope.occupancy()` keeps a trade only when `exit > entry`**, and that is deliberate: a trade
  with no interval cannot be displaced by a null model, has no blind window of its own duration to be
  matched against, and occupies no bars to count as exposure. It is also why the panel's reported
  trade count is larger than the tested one — see `simulate/README.md`.
- **`envelope.periods()` gives a calendar semester an identity independent of when a market's data
  starts.** That is what lets `model/trade_models.semester_shift()` displace 2013H1 the same way in
  every market, which is what makes `simulate/joint.py` correctly sized.
- **`curves.py` never adds two markets together.** Every market runs its own independent account, on
  its own dates, with its own real sizes. Combining them is `simulate/portfolio.py`, where the
  drawdown of a combination has to be computed on the combined curve and never summed from the parts.
- **`units.py` converts, it does not format.** `dollars()` multiplies by the entry price and the
  size; `scaled()` divides by the market's median ATR as a fraction of price — the same constant
  `backtest.run()` divides `mean_r` by, so the two are on one axis. That arithmetic is why it is here
  and not in `render/`: `simulate/paired.py` needs it, and `simulate/` importing `render/` would
  invert the study's one direction. The alpha of Test 1b is reported in five units because 0.00042 is
  unreadable, and the one to read first is **dollars accumulated over the whole sample**: how much of
  the money the strategy made was put there by *when* it entered rather than by being in the market.
- ⚠️ **`units.LABELS` has no consumer.** The panel prints its unit names from its own literals. It is
  left in place rather than removed, and recorded here, because this reorganisation moves code and
  does not change it.
