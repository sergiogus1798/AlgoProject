# retest/verdict — given those numbers, what do we conclude?

The inference layer. It is organised by **the four questions a risk committee asks, in order**, not
by test name: a test earns its place here by the question it answers, and one that answers none is
not added however standard it is.

**Imports from:** `core/`, `inputs/`, `model/`, `measure/` · **Consumed by:** `render/`, `explorer/`
**Must not contain:** a file read, or the production of any number it judges

| file | what it does | run it | in → out |
|---|---|---|---|
| `fragility.py` | **Question 1 — how much does it hurt?** Tail quantiles with exact intervals, the conditional drawdown the gate reads, the equity envelope, and the share of trades spent under water | imported | metrics + P/L → tail, fan |
| `modes.py` | **Question 2 — does it decay, or collapse?** Whether the outcome is one regime or two, how far from normal it is, and whether the strategy still traded | imported | metrics → shape, collapse |
| `attribution.py` | **Question 3 — what breaks it?** Which task's damage is real against the `bar` control, and Benjamini-Yekutieli across the pool | imported | metrics → attribution |
| `evidence.py` | **Question 4 — do I believe it?** The retest sims' own Sharpe against a benchmark, the analytic PSR of the original P/L against the same benchmark (0 here — OPEN.md #71, `POSSIBLE_IMPROVEMENTS.md` #10), effective bets, the corrected p-values and rank stability | imported | metrics + P/L → evidence |
| `gates.py` | Every threshold in the study, and what only warns | imported | body → flags |
| `scoring.py` | Sub-scores, composite and verdict tier | imported | body + flags → verdict |

## Two guards that decide whether a test may run at all

Both were learned from the data on 2026-09-18, and both replaced a first version that was wrong.

**A task must produce a distribution before anything distributional is said about it.** The test is
the **share** of simulations giving distinct results, not their spread and not their count, because
the failure has two shapes:

| task | distinct results per 1,000 | what it means |
|---|---|---|
| `mindist` | **1** | the stops sit far from price; the broker never refuses one, so nothing was perturbed |
| `bar` | 2-3 | shifting the start by up to 500 bars changes only whether a couple of early trades happen |
| `exits` | 2-6 | **this fleet carries no stop, target or trailing** — its exits are bar-count, so a ±15% jitter usually rounds to the same bar |
| `spread` | 69 | SQX samples from a grid; 1,000 runs land on 70 values |
| `slippage` | 100 | the same |
| `params` | 392-1,000 | genuinely continuous |
| `ohlc` | 997-999 | genuinely continuous |
| `stress` | 999-1,000 | genuinely continuous |

A count-based guard let the grid-sampled pair through, and the dip test then rejected unimodality on
**every strategy** for both — reading the gaps between grid points, not the strategy. A share-based
guard keeps the dip on the three tasks whose output really is continuous. The right analysis for a
grid-sampled task is a dose-response curve of the result against the parameter, which this study
does not do yet; `POSSIBLE_IMPROVEMENTS.md` carries it.

That `mindist` and `exits` barely respond **is itself the answer** for those axes, and the report
says so plainly rather than scoring them as passes.

**A quantile gets an exact interval, never BCa.** The first version bootstrapped the 5th percentile
with BCa and got `NaN` back on 5 of the 8 tasks. That is not a tuning problem: BCa is built for a
smooth statistic, and a quantile can only land on a handful of neighbouring sample values, so its
bootstrap replicates are heavily tied, the bias-correction term reads a replicate fraction of 0 or
1, and z0 goes infinite. The count of points below a true quantile is binomial, so its bounds give
the bracketing ranks directly — exact coverage, no resampling, and it cannot fail.
`fragility.bootstrap_mean()` keeps BCa for the smooth statistics it suits.

## Contracts and traps

- **The conditional drawdown is the gated number, not the 95th percentile.** It is coherent,
  subadditive, and it moves when the tail is heavy or has two modes — which is exactly when a
  percentile stops meaning what it appears to mean. The percentile is reported beside it.
- **Trades under water, never time.** A simulation file carries no dates. Leaving the word "time" in
  the vocabulary guarantees someone eventually reports one number as the other.
- **The equity fan's x-axis is normalised progress, not the trade index.** Simulations differ in
  length — 676 to 2,031 measured — so there is no common trade number to stack them on.
- **The trade count is a gated response, not a diagnostic.** A simulation that fired six times is not
  a degraded strategy, it is a different one, and its net profit is meaningless in every percentile
  it contributes to.
- **Nothing here reads a `.sqx` or computes a metric**; it judges what `measure/` wrote.
