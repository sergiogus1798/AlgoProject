# studies/screening/analysis — the maths over a whole population

Libraries, not commands. The entry points that use them live in `../reports/`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `metrics.py` | Reads a metrics export, works out which columns are IS, which are OOS, and which pair up, and drops rows that agree on every OOS metric -- the same backtest exported under a different strategy name | imported | `metrics.csv` → numeric columns + metric name lists |
| `correlations.py` | Pearson/Spearman, the single-test significance floor, and Benjamini-Hochberg over a family of tests | imported | two columns → correlation rows |
| `improvement.py` | Sweeps candidate IS filters: what each one does to an OOS outcome, with a bootstrap interval on the difference | imported | columns + one target → one row per filter |
| `replication.py` | Whether a conclusion drawn on one sample holds on another independently generated one: outcome gaps, filter thresholds carried across, rank stability | imported | two samples' columns → gaps and agreement |
| `decay.py` | How much of each strategy's in-sample edge survived, whether what is left beats its own error bar (Lo 2002 on the daily curve, annualised at 252 days, SQX's own convention: `sqrt((1 + SR_annual² / 2 / 252) / years)` — fixed 2026-10-02, `knowhow/research/gate-t-scales.md`), and the keep/doubt/discard call | imported | daily equity → one row per strategy |
| `tradelevel.py` | The t of a strategy's mean trade, iid and at the AR(1) effective n, and each trade's P&L from the market's own drift over its hold — what the gate's `trade_t` and `drift_excess_t` are made of; `drift_term`, the four drift terms of R3 (a today's, b per calendar window, c the blind trade of the same hold sized 1/ATR, d both), and `t_skew_kurt`, the same t with the PSR's skewness-kurtosis standard error | imported | trades + bars → t per strategy |
| `centred.py` | The maths the gate centres on its population: yearly-count overdispersion with part-year exposure, the log rate ratio and its error, the capped population median, and the per-strategy slope and mean of a per-trade column in time at the AR(1) effective n | imported | counts, per-trade table → z, slope |
| `onepass.py` | `edge_mean`, `t_cost`, `t_without` and `mae_pct`: the edge over the cost charged, R3's t under a cost stress and without the best quarter or trades, the MAE percentile in R. They reuse the t of `tradelevel` | imported | per-trade table → facts |
| `dataquality.py` | `mark()` flags the oos1 trades that touch an anomaly of the feed's inventory between their entry and exit bars; `facts()` gives `ret_datos`, the Welch `t_a` and `n_afectadas` | imported | per-trade table + events → facts |
| `delay.py` | The one-bar delay: `excess()` reprices trades with their fills moved (`SHIFTS`: E+1, S+1, ES+1, E-1) at the original lots, minus the drift term over the moved hold — NaN for a trade whose entry would land on or past its exit; `measure()` gives per strategy and variant the retention, the paired t of original minus moved and level 1a's t on the moved excess, over the trades that exist under the variant; `worst()` picks the variant that keeps least | imported | per-trade table + bars + costs → ret, t_delta, t per variant |
| `resample.py` | The gate's two resampling tests on a strategy's own trades: `homogeneity`, the permutation p of Q across periods; `drawdowns`, maximum drawdowns of block-bootstrapped build trades at another mean; `root` / `stream`, a fresh-or-given root seed and one stream per identity | imported | per-trade arrays + rng → p, simulated drawdowns |
| `floating.py` | Max drawdown and worst day of the marked-to-market daily equity, worst trade MAE and net per year, all in R | imported | daily equity + trades → one row per strategy |

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
