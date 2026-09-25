---
q: monte carlo retest results in sqx, MonteCarloRetest_Simulation Orders.bin format, MonteCarloRetest_Results.xml confidence levels LevelStat, MCUseFullSample, MC retest method config lastSettings, one MC result per sqx
tag: 🔬  date: 2026-09-17  see: sqx-format/mc-retest-reconstruction, conditions/mc-retest-task, costs/mc-retest-ranges
---
# MC Retest stores each simulation's P/L vector only, plus 11 per-metric quantile levels
Per simulation: `int32 count` + count × `int32` P/L in cents, big-endian, chronological — no dates,
prices, MAE/MFE, size, direction. A confidence level is a **per-metric marginal order statistic**, not a
simulation: the "95 %" row's NetProfit and Drawdown come from different simulations — never read a row
as one scenario. One `.sqx` holds exactly **one** MC result (re-run overwrites). ⚠️ `MCUseFullSample=true`
≠ OOS seen: check `NumberOfTrades` in sample 20 of the main result.

## Evidence
- Measured on the 10 `.sqx` of `XAUUSD/databanks/MC Random IS` and `MC Random IS 2.0` (4,896 sims).
  New members under `Results/Main: <SYMBOL>_<feed>/`: `MonteCarloRetest_Results.xml`,
  `RobustnessOriginalOrders.bin`, one `MonteCarloRetest_Simulation<N>Orders.bin` per sim.
- `size == 4 + 4*count` on 4,896/4,896. `RobustnessOriginalOrders.bin` = same format for the original;
  its sum ≈ `NetProfit` (24,268.56 vs stored 24,269.22, `Strategy 1.19.29`, 763 trades).
- Indices contiguous, truncate at the tail, never holes: 3 runs stopped at 499 / 440 / 457 of 500, all
  `0..n-1` → a short run is lost sample, not selection bias.
- XML: one `SQStats` (152 metrics) for the original + eleven `LevelStat` blobs, levels 50, 60, 70, 80,
  90, 92, 95, 97, 98, 99, 100. Level blobs carry 148 (no `DataLength`, `MaxNewHighDurationFrom/To/Pct`);
  **97 vary** with level, 51 constant (WF and Add-Markets holes, `Fitness`, `Complexity`,
  `ParameterCount`, `TotalDataDays/Months/Years`, 34 always-zero). One direction, one sample only.
- Level `L` of metric `m` = value at rank `n*(100-L)/100` of sims sorted worse-last; reconciled on 9/10
  files to < 1 unit (NetProfit and Drawdown). The 10th was the 499-sim run, table written over 500 (rank
  shifted by one).
- ~61 date/price metrics (`AvgBarsInTrade`, `Exposure`, `BiggestMAE`, `TotalMFE`, `Efficiency`,
  `EdgeRatioInPips`, `ExitQuality`, `RExpectancy`, `Stagnation`, `MaxNewHighDuration`, `TotalTradingDays`,
  `CAGR`, `ProfitableMonthsPct`, `EquityAngle`, `AmbiguousTrades`, `OpenDrawdown`, `MaxTSIntradayDrawdown`,
  `SortinoRatio`, `ProbSharpeRatio`) vary across levels: computed per sim, individuals discarded; the 11
  quantiles are the only MAE/MFE/duration channel for a retest.
- Config: `lastSettings.xml` `<MonteCarloRetest>` lists all ten methods with `<Params>`, used or not:
  `RandomizeExitParameters` (bentra's script), `RandomizeHistoryData` (by tick),
  `RandomizeHistoryDataFixedRange`, `RandomizeHistoryDataOHLC`, `RandomizeMinDistance`, `RandomizeSlippage`,
  `RandomizeSpread`, `RandomizeStartingBar`, `RandomizeStrategyParameters`,
  `RandomizeStrategyParametersCustomizable` (switches Period, Shift, Constant, OtherParam, ExitUsed,
  ExitUnused, Boolean, TradingOptions); plus `<NumberOfSimulations>`, `<MCUseFullSample>`, `<MCBacktestPrecision>`.
- Both XAUUSD databanks: `MCUseFullSample=true`, ran `2008.01.01 - 2017.12.31`, sample 20 empty in all 5 —
  "full" widens to the strategy's own split; IS-only retest → full is IS.
- Same five strategies, different method sets, each file only its own → isolating methods costs one
  databank per method.
