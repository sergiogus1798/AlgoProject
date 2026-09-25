---
q: walk forward matrix results in sqx, WalkForwardMatrixResult, RunResult stats statsOOS, WFM cell sample 10 20 127, WFM parameter stability SpecialValuesMap, futurePeriod empty RunStats, WFM optimisation population stored
tag: 🔬  date: 2026-09-10  see: export/wfm-export, conditions/wfm-acceptance, sqx-format/optimization-profile-bin
---
# The WFM grid lives in settings.xml; take cell metrics from `<Result>` blobs, never `RunResult/stats`
Under `<WalkForwardResult type="…WalkForwardMatrixResult"><MatrixResult>`; `core/wfmatrix.py` reads it.
⚠️ `RunResult/stats` is the FULL period (= sample 127), not IS; `statsOOS` = sample 20. Cell `<Result>`
samples: **10** first optimisation window, **20** all WF runs concatenated, **127** both. The last step
of each cell has no `RunStats` (`futurePeriod="true"`) — drop those rows. The optimiser's per-step
population is **not stored**; the closest is the 360 walk-forward steps.

## Evidence
- `MatrixResult` axes as ranges: `start1/stop1/increment1` OOS %, `start2/…` number of runs;
  `periodType=10` = **rolling** (IS and OOS constant length, slide). One `<RunResult>` per cell (5×6 = 30
  on XAUUSD) with settled params, `stats`, `statsOOS`. `<Periods>` → one `<WalkForwardPeriod>` per step:
  `optimizeFrom/To`, `runFrom/To`, `futurePeriod`, `testParameters`, `OptimizationStats` (IS) and
  `RunStats` (OOS). 30 cells × 12 steps = 360 steps, 1,212 blobs, 2.9 MB XML.
- `<Result>` has 15 blobs: direction (0 both, 1 long, −1 short) × sample. Additivity on two strategies:
  532 + 559 = 1,091 trades; 2,389 + 4,185 = 6,574 days. Samples 11 and 21 duplicate 10 and 20 here.
- `SpecialValuesMap`: `ParametersStability_WF_<runs>_runs_<pct>_OOS` per cell, `AvgParametersStability`,
  `WorstParametersStability`, `FiltersResultFailedReason` (verdict in words), `WalkForwardConditions`,
  one `MEC_FULL_WF_<cell>` sparkline JSON for the chosen cell.
- WF-only columns `WFPctOfProfitableRuns`, `WFMaxProfitByRunInPct`, `WFMinTradesInRun`, `WFMaxPctDDbyRun`
  (`resultType="WalkForwardMatrix"`, `subresult` 30/31/33) are not stored — recomputed from the matrix,
  derivable in Python from the steps table.
- Population: `<MaxTests>10000</MaxTests>` in `lastSettings.xml`; only the winner survives. Re-running WFM
  with the 3D-charts setting off gave a structurally identical `settings.xml` (same 360 periods, 1,212
  blobs). That setting only governs `optimizationProfile.bin` (SPP / sequential opt), which WFM lacks.
