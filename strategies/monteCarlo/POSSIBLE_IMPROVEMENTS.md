# Possible improvements — Monte Carlo robustness

What was considered and deliberately left out of the first build, so the reason does not have to be
rediscovered. Nothing here is a bug. Ordered by how much it would change a conclusion.

## 1. The thresholds are the study, and three of them are provisional

Every number that decides lives in `gates.py` and `config.yaml`, which is what makes them arguable.
Three of them are not yet the owner's decision and the report says so:

- **The account-survival drawdown ceiling, 10%.** A placeholder until the prop-firm rules are known.
  Measured on `XAUUSD / Results` at 1,000 $ risk on a 100,000 $ account it vetoes 22 of 36
  strategies on its own. It is a **sizing** statement far more than a strategy statement: halve the
  risk per trade and the same strategies clear it. Deciding it is the prop-firm module's job.
- **The dead-block veto.** Any non-overlapping 24-month block whose bootstrap median is negative
  vetoes. On the same databank that is 30 of 36 strategies, and it is doing real work — those blocks
  are real losing periods — but a rule that fails five of every six candidates is a threshold
  question, not a finding. The alternatives: require the 5th percentile rather than the median,
  allow one bad block in N, or scale the window to the trade cadence.
- **The Family D sub-score saturates at zero** on this data, because it takes the worst of three
  parts and the worst non-overlapping block's 5th-percentile profit factor is almost always below
  1.0. It is faithful to the specification and currently carries no information across strategies.
  Either the curve's endpoints move, or the part does.

## 2. What the trade export cannot say

The specification asks for `StopLoss`, `ProfitTarget`, `BarsInTrade` and a per-trade `CommSwap`
column. SQX's `orderstocsv` writes none of them (`knowhow/04-export.md`). What was done instead:

- **Cost is recovered**, `gross − net`, which is better than a modelled cost: it is what was
  actually charged. The modelled commission is kept only as a cross-check.
- **Swap as a percentage of price is not modelled separately.** It is inside the recovered cost, so
  `cost_shock` scales the two together. A separate swap axis would need the overnight count per
  trade, which the export does not carry either.
- **No stop or target is confirmed from the file**, because the columns do not exist. For the XAUUSD
  fleet that matches what the templates build (no stop, no target), but it is an assumption
  inherited from elsewhere rather than a check made here.

## 3. Modelling that would change an answer

- **A regime null, not only a regime split.** Family D compares terciles of daily volatility, but a
  bucket with a low profit factor might simply hold fewer trades. Resampling trade *dates* within a
  regime would say whether the bucket difference is bigger than the sampling noise of the split.
- **Volatility-normalised P&L** as the response variable, as the specification suggests optionally.
  It is more stationary, and it changes what "the edge lives in high volatility" means.
- **Stationary bootstrap for the windows.** They currently use the i.i.d. bootstrap, which is the
  independence baseline. Inside a two-year window the block version would be more honest and is one
  argument away.
- **The stitched path picks the 5th percentile of every segment.** How adversarial that is has no
  principled answer; 1% or 10% would be as defensible, and the number is a knob nobody has argued
  for yet.
- **The skip test zeroes a trade instead of removing it.** Net profit and drawdown are identical
  either way and no floor of that test reads the trade count, but the Sharpe of a skip simulation is
  diluted and must not be quoted.

## 4. Compute

- **Stability runs once per databank, on the strategy with the most trades**, not once per strategy.
  It measures whether `n_sims` is high enough, which is a property of the run rather than of a
  strategy — but a short strategy's tails are noisier than the reference's, so the figure is
  optimistic for them. Per-strategy stability is a flag away and multiplies the runtime by
  `n_stability_runs`.
- **The compounding reporting view of §2.4 is not built.** Additive fixed risk is the basis of every
  number here; a compounded view would be a second rendering that no gate reads, and nobody has
  asked to see one yet.
- **The optional bootstrap CI on the PSR is not built** for the reason the specification gives: it
  double-counts the sampling uncertainty the PSR already models, and the surplus compute is better
  spent running whole databanks.

## 5. The regime terciles do not move between runs

The stability check was specified to point at the volatility-tercile boundaries too. It does not,
because there is nothing to measure: ATR is deterministic and a GARCH fit on a fixed history
converges to the same parameters every time, so the boundaries are identical run to run. What could
move them is the **data** — one more month of bars shifts every tercile — and that is a different
check: re-tag the same trades under a rolling estimation window and see whether any trade changes
bucket. That is worth building and is not what was asked for.
