# retest/model — what does a number read off a simulation actually mean?

The modelling layer. A simulation file carries one thing: a vector of P/L in cents. Turning that
into "this run's drawdown was 12.9%" is not arithmetic, it is a **choice of definition**, and SQX
made those choices before we did. This folder holds the definitions, calibrated against SQX's own
stored answers rather than guessed from the metric names.

It is separate from `measure/` because the two answer different questions: this layer says *what a
metric is*, `measure/` says *what its value was on these runs, and whether that reconciles*.

**Imports from:** `core/` and `inputs/` · **Consumed by:** `measure/`, `verdict/`, `render/`
**Must not contain:** a file read, a threshold, or a p-value

| file | what it does | run it | in → out |
|---|---|---|---|
| `recon.py` | **The registry.** The 30 reconstructible metrics, which way each one ranks, and the declaration of what the other 118 are | imported | P/L + offsets → one value per simulation |
| `counts.py` | The metrics that are reductions over the trades: totals, counts, averages and their ratios | imported | parts → arrays |
| `drawdown.py` | Every drawdown metric, and the account-capital denominator the four of them share | imported | parts → arrays |
| `runs.py` | Streaks of wins and losses, and the runs test SQX scores their randomness with | imported | parts → arrays |

## The calibration, and why it is not optional

Six of these formulas do not mean what their names suggest. Every one below was established by
running the candidate over the original backtest and over the eleven stored confidence levels of
all eight tasks — **12,210 checks, 16 disagreements, all single-level rank ties** (2026-09-18).

- **`StandardDev` is `ddof=0`**, the population deviation. With `ddof=1` the worst error against the
  stored tables is 0.47; with `ddof=0` it is 0.008. `core/significance.py` uses `ddof=1` for a
  different job and the two must not be harmonised.
- **`SQN` caps the sample-size factor at 100 trades** — `sqrt(min(n, 100))`, not `sqrt(n)`. On 763
  trades that is 0.77 against the textbook 2.12, a 176% error.
- **`WinLossRatio` is a count ratio**, wins over losses. The ratio of *mean* win to *mean* loss is
  **`PayoutRatio`**, a separate column. They are not two names for one quantity, and `KellyFormula`
  uses `PayoutRatio` as its R.
- **`AvgLoss` is stored positive.** A signed reconstruction is out by a factor of two.
- **Drawdowns are measured against the account**, capital plus the peak in force, never the peak
  alone: 5.52% against 195% on the calibration strategy. `AvgDrawdown` averages over **every** trade
  including the zeros — averaging only the trades in drawdown is out by 11%, averaging episode
  maxima by 67%.
- **`RecoveryFactor` and `ReturnDDRatio` are not synonyms.** The first divides by the
  capital-relative fall, the second by the absolute one: 4.40 and 3.86 on the same run.
- **`ZScore` carries a +0.5 continuity correction.** Without it the reconstruction misses by exactly
  `0.5 / sigma` every time.

## Contracts and traps

- **`HIGHER_IS_WORSE` is not decoration; without it eleven metrics reconcile backwards.** A
  confidence level is an order statistic, so every metric needs a direction, and the losing half of
  the table runs the other way: level 100 of `Drawdown` is the *deepest* fall while level 100 of
  `NetProfit` is the *smallest* profit. Getting this wrong was a real bug here, and it showed up as
  relative errors of 0.88 to 0.94 on exactly the loss and drawdown metrics.
- **`MaxLoss` is in that set, and the consequence is a trap for the reader**, not just for the code:
  SQX's level-100 `MaxLoss` is the worst trade *closest to zero*, so a high-confidence `MaxLoss`
  read as a stress number is backwards.
- **Only 30 of the 148 metrics are here, and the other 118 are declared, not forgotten.** `ANALOGUE`
  names the five SQX computes on the **daily equity curve** — `SharpeRatio`, `SortinoRatio`,
  `UlcerIndex`, `RSquared`, `Stability` — which no simulation file carries; a per-trade version is a
  different object and travels under a different name. `EXCLUDED` names `AvgAbsTrade`, which sits at
  a constant ratio of 1.00215 to `mean(|pnl|)` with no formula found. `measure/integrity.py` asserts
  the partition, so "absent from `RECON`" can never be read as "unimportant".
- **`parts()` is the shared signature.** Every function in `RECON` takes the dict it returns and
  gives back one value per simulation. The path-dependent metrics — drawdown and streaks — loop per
  simulation, because a running maximum does not reset at a segment boundary on its own; everything
  else is a `reduceat`. Adding a metric is a function, a row in `RECON`, and a direction if it is a
  losing one. Nothing else changes.
- **Simulations have different lengths** — 676 to 2,031 measured — so the layout is a flat array
  plus offsets, never a matrix.
