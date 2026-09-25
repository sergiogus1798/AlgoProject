---
q: storage format parquet vs CSV for exports; which columns to drop SPP export; redundant metrics; RExpectancy 99999 sentinel; CalmarRatio? question mark column name
tag: 🔬  date: 2026-09-23  see: export/trade-export-columns, export/spp-export, export/what-a-project-stores
---
# Change the format, keep the columns: one typed zstd Parquet per test and export
- `.sqx` is the source, an export a projection. One file per test+export, never per strategy. Wide for parameters/statistics, long for trades.
  Categorical `strategy`/`Symbol`/`Sample type`/`result`/`sample`; money `int32` cents or `float32` where already. Intermediates (`raw/` CSV, staged `.sqx`) die with the export. `metrics.csv` stays CSV (human-read).
- Drop only the 42 constant SPP columns; keep redundant pairs across windows (`NetProfit` vs `CAGR` diverge between 10-y IS and 5-y OOS).
- ⚠️ Filter `RExpectancy` sentinels (`core/surface/dedupe.drop_sentinels`, `|v| > 100`) before any ranking.
- ⚠️ `CalmarRatio?` and `AnnualPctReturnDDRatio?` have a literal `?`; without it → all-NaN column, no error.

## Evidence
- Full analysis: `docs/AgentPDFs/almacenamiento-datos-2026-09-23.md`. 118 cross-market CSVs → one 4 MB `trades.parquet`; SPP long param table 34 MB RAM vs 6 MB wide (21,205 × 8).
  `raw/` 346 MB / 270 files → 112 MB / 123. 📓 Studies re-ran with identical verdicts (sppUltra, WFM); cross-market readers reproduce `backtest.setting` on all 3 markets.
- `raw/XAUUSD/SPP_IS/2026-09-10/`, 21,205 × 154: CSV 39.67 MB · Parquet 154 cols 5.72 MB (6.9×) · CSV 29 cols 9.87 MB · Parquet 29 cols 1.51 MB (26×).
  Trades (763): CSV 134.2 KB → Parquet 16 cols 42.4 KB → 8 cols 29.8 KB. Dropping loses `MAE ($)`/`MFE ($)` (used by `strategies/`, not reconstructible).
  SPP permutations threw trades away: their 152 numbers are all that exists; a lost column = re-run SQX.
- 42 constant of 152: four `AddMarkets*Median`, `BestWF`, `EdgeDecayRatio`, `Parameters`, `SlopeRatio`, three `TotalData*`, 34 unfilled `stat:f:NN` / `stat:i:7` / `stat:l:2-3`.
  Of 110 varying, 85 unique; 25 redundant at |rho| > 0.999 within one window:
```
AHPR = AnnualPctReturn = AvgPctProfitPerYear = AvgProfitPerDay = AvgProfitPerMonth
     = AvgProfitPerYear = CAGR = NetProfit = NetProfitInPct
AnnualPctReturnDDRatio? = CalmarRatio?        AvgTrade = Expectancy
AvgTradesPerDay = AvgTradesPerMonth = AvgTradesPerYear = DegreesOfFreedom = NumberOfTrades
Drawdown = DrawdownPctOnInitial = MaxTSIntradayDrawdown = OpenDrawdown
DrawdownPct = OpenDrawdownPct    Exposure = ExposurePosition    Outlier = Outlier2
PayoutRatio = TSWinLossRatio     WinLossRatio = WinningPct      ZProbability = ZScore
```
- Cross-window divergence is the same sqrt(T) bias that makes `Ret/DD` unusable across windows.
- `RExpectancy`: 99999.0 on 3 rows, −1.0 on 15, all ~one-trade permutations (0.08 %) — SQX "undefined". Argmax over 5,000 variants picks them. No other metric of the 41-column export has them.
