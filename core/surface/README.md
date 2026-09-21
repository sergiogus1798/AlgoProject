# core/surface — the maths of a parameter grid

A grid of parameter tuples measured in two windows. Not a databank, not a strategy: the surface
itself. `sppUltra` reads the grid SQX sampled, `walkForwardCorrelation` reads the grid we designed,
and `walkForwardMatrix` reads the one a cross-check produced — three consumers of the same
statistics, which is the bar `core/README.md` sets for anything statistical living here.

| file | what it does | in → out |
|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — |
| `dedupe.py` | How many independent observations the grid really holds: sentinel removal, distinct tuples, the effective n, and a bootstrap that resamples tuples instead of rows | grid → counts, intervals |
| `shift.py` | How far the surface moved between two windows: Hodges-Lehmann in units, Cliff's delta in rank, the quantile-quantile curve, the tail excess, and the dispersion ratio adjusted for sample size | two windows → displacement |
| `plateau.py` | How much of the grid works, and whether its best point beats what searching noise would have produced anyway: plateau area, half-max area, the noise maximum and the deflated Sharpe | grid → probabilities, thresholds |

## The two mistakes these exist to prevent

**Rows are not observations.** Inert parameters duplicate points — measured 2026-09-20 on
`XAUUSD/SPP IS`, `CBlock_SqzMmnInt21` gave 757 groups and all 757 agreed on NetProfit and trade
count to the last decimal — and the surface is smooth on top of that, with lag-1 autocorrelation up
to +0.89. An interval taken over 12,000 correlated rows is falsely narrow by roughly a factor of
three. **Everything here is fed `distinct()` output, and `n_eff` is what the thresholds see.**

**Distributions measure level; pairing measures order.** A surface that keeps its histogram while
its ranking is reshuffled at random gives a Hodges-Lehmann shift of zero and has lost everything.
That is why `hodges_lehmann` is the paired estimator and why the golden test for it is the shuffled
grid: level statistics alone are blind to the failure that matters most.

## Traps in the data these read

- ⚠️ **`RExpectancy` carries sentinels**, not measurements: `99999.0` on 3 rows and `-1.0` on 15,
  all of them permutations with about one trade (measured 2026-09-20). They are 0.08% of the grid
  **and they win the argmax over 5,000 variants**. `drop_sentinels` runs before any ranking.
- **The unit trap in `deflated_sharpe`.** SQX stores annualised Sharpes; `core/significance.py`
  works per observation. Mixing them yields a plausible-looking number that means nothing. The
  signature says which unit it wants and the caller converts.
- **`hodges_lehmann` subsamples above 4,000 pairs**, with a fixed seed. The estimator is quadratic
  in n and the grid is not; a report regenerated tomorrow still gives the same interval.

`variance_factor` comes from `core/significance.py` rather than being written again here. That
formula appearing twice is a correctness risk, not a typing one — a fix to one copy leaves the other
quietly wrong.
