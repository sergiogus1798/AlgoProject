# studies/screening/analysis — the maths over a whole population

Libraries, not commands. The entry points that use them live in `../reports/`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `centred.py` | What the gate reads against its own population's centre: the change of trading rate from the build to oos1, the slope of a per-trade column in time. | imported | counts, per-trade table → z, slope |
| `correlations.py` | Correlate in-sample metrics against out-of-sample outcomes, and say which results survive. | imported | two columns → correlation rows |
| `dataquality.py` | Data quality (spec 6.6): how much of the edge lives in trades that touch a feed anomaly. | imported | per-trade table + events → facts |
| `decay.py` | Per-strategy decay: how much of the in-sample edge survives, and whether what is left is real. | imported | daily equity → one row per strategy |
| `delay.py` | What a strategy's per-trade excess keeps when its entry, its exit or both fill one bar off. | imported | per-trade table + bars + costs → ret, t_delta, t per variant |
| `floating.py` | What a strategy's worst stretches cost, in units of its risk per trade (R). | imported | daily equity + trades → one row per strategy |
| `improvement.py` | What an in-sample filter buys out of sample, and how many strategies it costs to get it. | imported | columns + one target → one row per filter |
| `metrics.py` | Load a metrics export and work out which of its columns pair in-sample against out-of-sample. | imported | `metrics.csv` → numeric columns + metric name lists |
| `onepass.py` | R5c, R8 and R9b: edge against cost, the t without the best, and the typical bad MAE. | imported | per-trade table → facts |
| `permuted.py` | numpy's `Generator.permuted` and its sums inside one numba kernel: the gate's Q under shuffles, no matrix held. | imported | centred trades, period starts/sizes, PCG64 rng → one value per shuffle |
| `replication.py` | Does a conclusion drawn on one sample of strategies hold on another, independently generated one. | imported | two samples' columns → gaps and agreement |
| `resample.py` | The gate's two resampling tests on a strategy's own trades: homogeneity across periods, and the drawdown its build makes expectable. | imported | per-trade arrays + rng → p, simulated drawdowns |

The excess over chance and Benjamini-Hochberg moved to `engines/inference/` (2026-09-25): the
gate and the monkey reading need them as much as these do.

Two things these enforce, because both have already produced wrong answers:

- **A constant column is dropped, not reported as NaN.** SQX leaves some metrics at one value for
  a whole population (`PSR` and `Symmetry` did this in the previous project). `measured()` excludes
  them, so they never reach a correlation.
- **The significance floor is not the threshold.** At n=10,000 a correlation clears the ordinary 5%
  level at |r| > 0.02. Every in-sample metric is tested against the same outcome at once, so
  `discoveries()` controls the false discovery rate across the family instead.
- **Rows are not strategies.** `metrics.csv` exports no trade list to hash, so `deduplicated()`
  drops a row that agrees with an earlier one on every OOS metric at once before anything is
  counted or correlated -- 🔬 52 of 9,948 on `XAUUSD/OOS` 2026-09-29, 0 of the compared `SPP_OOS`.
  `isOos.report`, `filters.report` and `replication.report` all call it; `decay.report` does the
  equivalent on the daily equity curve itself, since it reads `.sqx` directly and never loads
  `metrics.csv`.

Spearman leads every ranking. These metrics are heavy-tailed and one blow-up strategy moves Pearson
a long way; where the two disagree, suspect outliers.

`improvement.py` turns a correlation into a decision. The three rules it holds to, all decided with
the owner and none of them adjustable per report:

- **What good means out of sample** is the target's own median plus the share above break-even —
  break-even is 1.0 for profit factor and 0.0 for everything else, since Sharpe and Ret/DD go
  negative when a strategy loses. The default targets are Sharpe Ratio (OOS) and Ret/DD Ratio (OOS).
- **A filter leaving fewer than 200 strategies is not judged at all.** A filter down to a dozen
  survivors can show a huge improvement and mean nothing, so the floor is a stated rule rather than
  a call made per report.
- **Only single clauses are swept**, each metric at the 5/10/20/30/50% cut from both ends. Two
  clauses ANDed is a different search space and needs a different correction. The 5% cut was added
  on 2026-09-04, after the first sweep found the improvement still rising at its tightest cut and so
  could not say where it stopped paying; at 5% on XAUUSD it visibly flattens.

- **The bootstrap p must be able to reach Benjamini-Hochberg's first rung.** Its floor is one over
  the resamples drawn, and the lone best of m filters is named only at p ≤ 0.05 / m. 🔬 2026-10-04:
  at 2,000 resamples and 210 filters the floor (0.0005) sat above that rung (0.00024), so one or
  two filters on the floor — a weak monotone effect seen only at the two 50 % cuts — could never be
  named. `lift()` now redraws a filter none of whose first 2,000 resamples cross zero up to
  `reach(m)`, the first multiple of 2,000 above m / 0.05 (6,000 at m = 210), in blocks of 2,000 so
  memory is unchanged; every other filter keeps its first-pass numbers bit for bit. Cost on
  9,897 strategies × 210 filters with 175 on the floor: 2.3 s per outcome, from 1.3-2.4 s.

`replication.py` answers the question `improvement.py` cannot: whether a filter chosen on one
population still delivers on a different one. Two traps it exists to avoid:

- **Do not compare correlations across differently selected samples.** A sample generated with
  "Sharpe (IS) top 10%" as an acceptance condition has almost no variance left in Sharpe, so its
  Spearman against any outcome collapses — by construction, not because the conclusion failed.
  `restriction()` measures that narrowing and the report flags it; the comparison that means
  something is the **outcome**, via `hit_gap()` and `carried()`.
- **Thresholds travel, quantiles do not.** `carried()` takes the reference's cut in the metric's own
  units and applies that number to the other sample. Re-taking "the top 10%" inside an already
  filtered sample would be a different, stricter filter wearing the same name.

- **The reference's best filters are chosen among those the sweep would judge** — at least
  `MIN_SURVIVORS` (200) kept on the reference; on a reference under 400 strategies there is none
  and the report says so. The promise is still the maximum of the judged filters' hit rates, so it
  is optimistic by selection: a mildly negative Δ on every sample is what a null would show.
- **An empty sample is NaN, not a number.** When no strategy of a sample clears a carried
  threshold, `hit_gap()` returns NaN for the gap and its interval, and `carried()` n = 0.

Near-duplicate filters move together: six overlapping filters agreeing that a sample beat its
prediction is one observation, not six. Read the interval on the difference, not the row count.
