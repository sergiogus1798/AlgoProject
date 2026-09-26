---
q: Walk Forward Matrix acceptance decoded; where WFM conditions live; cell score robustness thresholdPct robCombRows robCombCols robMinComb; subresult 30 31 32 33 Stability Score WFScore; WFM failed strategy kept with DeleteFailedStrategies false FiltersResultFailedReason; calibration of SQX default WFM conditions
tag: 🔬  date: 2026-09-26  see: conditions/wf-type, export/wfm-export, conditions/active-conditions-in-crosschecks
---
# WFM acceptance: only `<WalkForwardMatrix><AcceptanceSettings><Conditions>` counts; cell score = % active conditions met
- Cell passes if `round(met / active * 100) >= thresholdPct`; strategy passes if some `robCombRows × robCombCols` rectangle has ≥ `robMinComb` passed cells.
- Zero active conditions → score 100 → all pass. With active conditions it FILTERS (independent of `DeleteFailedStrategies`); map mode = `robMinComb: 0`.
- Pass map is not stored; `core/wfmatrix.py` recomputes it; `.sqx` `SpecialValuesMap` → `WalkForwardConditions` holds the criterion used.
- SQX default thresholds don't fit this population; the project's are in the `wfm:` block of `assets/_build.yaml`.

## Evidence
Decompiled `internal/libs/SQTradingLib.jar` (SQX's `j64/bin/javap`) + `internal/plugins/CrossCheckWalkForwardMatrix/`.
- Master project: `<Conditions thresholdPct="80" robCombRows="2" robCombCols="2" robMinComb="0" />` EMPTY; its 9 apparent conditions hang off the sibling `use="false"` `WalkForwardOptimization`.
  All 5 `XAUUSD/databanks/WFM` strategies store an empty `WalkForwardConditions` → that WFM ran with no criterion; `FiltersResultFailedReason` = `Passed`.
- `WalkForwardResult.computeRobustnessScore`, `WalkForwardMatrixResult.findBestGroupOfPassedCombinations`: `use="false"` not in denominator.
  Rows = number of runs (Param2), columns = OOS % (Param1) (`createMatrix`); 4×4 on 6×5 fits 6 positions. Rectangle doesn't fit → best cell counted as one → only `robMinComb <= 1` passes, silently.
  Centre of best rectangle = GUI "Recommended combination: reoptimizing every X days on history of Y days".
  Filter message: `Cross Check filter in 'WF matrix': Robustness score didn't pass.` (`WalkForwardCrossCheckMethod.checkConditions`, `dismissalReason`).
- 🔬 2026-09-26, custodian, 2 strategies, area forced impossible (16 of 16 at 100 %) and
  `DeleteFailedStrategies=false`: **both stayed in the output databank**, each with
  `settings.xml <FiltersResultFailedReason>Cross Check filter in 'Walk-Forward Matrix': Robustness
  score didn't pass.`; with the real 12-of-16 they carried `Passed`. A fail marks, it does not delete
  — `core.sqxfile.sqx_filter()` reads it, `export_wfm` stores it (`status.parquet`, `failed_in_sqx`).
  Cosmetic bug: printed `MinResults:` reads `robCombCols` not `robMinComb` (log text only).
- `getStatsValue` reads `subresult` (def 30), `direction` (0), `sampleType` (def 127), `plType` (10):

| subresult | family | source | uses sampleType |
|---|---|---|---|
| 30 | `WF <metric>` | cell `stats(direction, plType, sampleType)`: 20 = concatenated OOS runs, 10 = first optimisation, 127 = all | yes |
| 31 | `WF Stability <metric>` | `statsStability` | no |
| 32 | `WF Score of <metric>` | `statsScore` | no |
| 33 | `WF Special …` | `statsSpecial`; forced for SQX's own columns | no |

- Stability = Σ metric in OOS parts / Σ in optimisation parts ×100, excluding last step (no OOS); `dependentOnTradingPeriod` columns (NetProfit, # trades, abs Drawdown, Stagnation) divided by days first → compares rates.
- Score = whole-WF metric / original backtest metric (portfolio, sample 127) ×100 — "does reoptimising help?". ⚠️ `WFScore` column ≠ Score: it is `wfResult.scorePerc` = % conditions met.
- `resultType` must be `WalkForwardMatrix` (or any walk-forward: shared base class, same `WalkForwardResult`) — `ProjectConfigHelper.getConditions` looks the plugin up by name.
- Stored per cell only: `param1`, `param2`, `testParams`, `resultName`, stats blobs (no `scorePerc`, `passed`).
- Calibration, 150 real cells (5 × 30) of `XAUUSD/databanks/WFM`, 2018–2022, share passing: `Stability NetProfit > 60` 1 % (median 8.6 %, max 73) ·
  `WFPctOfProfitableRuns > 70` 9 % · `WFMaxProfitByRunInPct < 50` 11 % · `WFMinTradesInRun > 20` 55 % (84 % at 6 runs, 36 % at 16) · `Stability Drawdown < 130` 57 % · `WFMaxPctDDbyRun <= 25` 100 %.
  NetProfit stability is low by construction (optimisation part chosen for being best); PF stability median 69 % → `_build.yaml` asks PF.
