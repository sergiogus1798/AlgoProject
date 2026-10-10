---
q: Does raising the monkey's `draws` reduce how many strategies pass by chance, and what does it cost?
kw: how many monkeys pass by simple random chance, reduce false positives in the monkey test, raising nulls draws, draws_needed, more random entry runs, monkey study cost vs SQX, distribuciones.parquet size, raw=False histogram tails, alpha times n expected passes, BH bar unreachable
tag: 🔬  date: 2026-10-09  see: perf/workflow-step-durations
---
# More draws does NOT lower the chance-passers (that is `alpha*n`); it only makes BH's bar reachable — and it costs DISK, not CPU
`engines.inference.excess`: `expected_all_null = alpha*n`, Storey's `pi0*alpha*n`. `draws` is in
neither — it sets the floor of the observable p, `1/(draws+1)`, against BH's rank-one bar `alpha/n`,
so `draws_needed = n/alpha - 1` (2,499 for 125 strategies, 99,999 for 5,000); below it nobody is
named at rank one, though BH steps up and k tests can clear `k*alpha/n`. What DOES lower them:
`fdr.discoveries` instead of counting passes, fewer looks (`core.surface.trials`), near-independent
tests multiplying (`alpha^k` — crossmarket, crossTF, oos2 do it), `snooping.stepm` on a correlated
family. Family-wise maxT is out: `nulls.simulate` seeds `_stable(key)`, one stream per strategy.

## Evidence
🔬 2026-10-09, on the measurements of `perf/workflow-step-durations` plus the parquets in
`AlgoData/reports`.
- The monkey is **~90x cheaper than one SQX step**: `crossmarket.report` 28.7 s wall (555 s CPU,
  19.3x parallel) for 8 strategies × 9 markets, against 2,580 s for MC Retest's 7 tasks on 8
  strategies. CPU was never the reason `draws` sat at 2,500.
- **The parquet is.** `core.study.draws` keeps the draws raw, 4 rungs × every reported statistic:
  132 MB measured at 2,500 draws (`Test_NIKKEI225_H1_aroonL_cal6/OOS/.../monkey`), 290 MB for a gate
  run. Raw at 100,000 draws would be ~40x that.
- So `engines/nulls/config.yaml` went to **`draws: 100000`** (floor p = 1.0e-5, resolves BH over
  ~5,000) and `studies.readings.monkey.one` records with **`raw=False`**: 200-bin histogram plus the
  100 exact extremes each side. The p is unaffected — `n_ge`/`n_le` are computed over the full draws
  before anything is stored.
- The gate's level 3c has its own knob (`studies/screening/gate/config.yaml`, `draws: 5000`) and was
  left alone: it runs over the whole build population, where the same multiplier is not free.
