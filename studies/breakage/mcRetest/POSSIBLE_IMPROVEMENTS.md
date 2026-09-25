# retest — where the design had real alternatives

Argue a change here, in writing, before making it in code.

## Deliberately left out, and why

Nine things the source plan asked for are not here. None was dropped for effort; each was measured
or reasoned to be wrong for this study, and re-adding one means arguing against the reason.

1. **Deflated Sharpe.** It needs the population of strategies tried during generation, which does
   not exist at this stage — and a thousand retests of *one* strategy are not a thousand selection
   trials. `monteCarlo/README.md` and `crossmarket/significance.py` already refuse it for the same
   reason. Feeding the simulations in as `N` would produce a credible, false number.
2. **Jarque-Bera's p-value.** Measured 40 of 40 rejections, the largest p being 0.014: its answer
   is known before it runs, and in the multiplicity pool it would spend the budget on certain
   rejections. Skew and kurtosis stay as descriptives.
3. **Levene.** `scipy.stats.levene(center="median")` *is* Brown-Forsythe. Running both is running
   one twice and doubling the multiplicity for nothing.
4. **KS as the headline.** The question is *which perturbation hurts more*; KS tests distributional
   equality and at 1,000 simulations returns p≈0 on every pair without saying which. Demoted to a
   reported number, out of the pool.
5. **BCa on a quantile.** Measured: `NaN` on 5 of 8 tasks. A quantile is an order statistic, its
   bootstrap replicates are heavily tied, and the bias correction goes infinite. The exact binomial
   interval is used instead — no resampling, guaranteed coverage, cannot fail.
6. **Kendall tau printed at five strategies.** The null has 120 points and the smallest two-sided p
   is 0.0167. It is built and gated at 20 strategies, and renders "no evaluable" below that.
7. **ENB choosing the FDR method.** It describes; Benjamini-Yekutieli is used unconditionally.
   Letting an ENB estimated from five short series pick between two procedures is letting noise
   decide. Measured, the ENB is 4.81 of 5 — which **refutes** the assumption it was added to
   confirm: a shared generation template constrains the shape of the rules, not the timing of the
   trades, and it is the second a correlation sees.
8. **`AvgAbsTrade`.** A constant ratio of 1.00215 to `mean(|pnl|)` with no formula found, and
   almost invariant between simulations.
9. **"Time under water".** A simulation file carries no dates. It is *trades* under water, and
   leaving the word "time" in the vocabulary guarantees someone eventually reports one as the other.

## Open, and worth building

- **A dose-response curve for the grid-sampled tasks.** Spread and slippage produce 69 and 100
  distinct outcomes from 1,000 runs because SQX samples them from a grid. No distributional test
  may run on a comb, so `modes.py` gates them out — but the right analysis was never a distribution
  in the first place: it is net profit *against the spread that produced it*, which would answer
  "at what spread does this stop working" exactly. That needs the sampled parameter per simulation,
  which SQX does not store, so it would have to be inferred from the outcome clusters.
- **The coherent scenario beside the marginal table.** A confidence level is a marginal order
  statistic per metric, so the "95%" row is not a run that happened. The whole metric row of the
  one simulation at that rank by a declared ordering metric is a different and more honest object,
  and showing the two side by side is the clearest demonstration of the trap. Not built.
- **The explorer panel.** `monteCarlo/` and `crossmarket/` both have one. Here the expensive half
  already happened at ingest, so it needs no cache — which is one fewer file and one fewer way to
  read a stored number as an answer to a question it was not computed for.
- **Charts.** The equity fan is computed (`fragility.fan`) and never drawn.

## Thresholds are unvalidated

Every cut in `gates.py` — `survival_dd_pct`, `exec_keep_frac`, `min_pf`, `collapse_frac`,
`psr_gate` — is a placeholder chosen to be plausible, not calibrated against the owner's real
account or prop-firm rules. On the first battery all five strategies failed. That may be the
strategies, and it may be the thresholds, and until someone calibrates them the report says so in
its own words rather than implying a verdict the numbers do not support.
