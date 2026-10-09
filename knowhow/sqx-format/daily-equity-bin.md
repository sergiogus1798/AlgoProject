---
q: How do I parse `dailyEquity.bin`: what does each daily value mean and which series is `Main`?
kw: parse dailyEquity.bin, is SQX daily equity the day's low or close, daily low equity MAE per day, daily equity curve without SQX, sub-period / split OOS study, which dailyEquity.bin (Main vs Portfolio vs AdditionalMarket), equity vs net profit mismatch, open position last bar, is daily equity mark-to-market, which day is the equity stamped, align equity with bars / benchmark, cross-check market curve sum vs NetProfit
tag: 🔬  date: 2026-10-04  see: export/archived-trades-vs-reclocked-bars, sqx-format/equity-reconstruction-usdjpy-gap, research/gate-t-scales, sqx-format/result-sections, sqx-format/sqx-zip-members, sqx-format/leg-curve-warmup
---
# dailyEquity.bin parses: each trading day's LOWEST equity (floating at the M1 wicks), cumulative; take `Main`
`core/sqxstats.equity(path, result="Main")`: one point per trading day, cumulative from the leg's start.
🔬 **Day D = the lowest equity reached during D on the feed's clock AT THE BACKTEST** (closed + open positions at their
worst M1 wick), **not a mark to market**: its differences are low-to-low, never daily P&L — rebuild MTM
from trades + M1 (`portfolio/common/construct/equity/`). 🔬 **Sampled only while a position is open** (2026-10-06):
a day that ends flat after an exit shows the worst wick BEFORE the exit, never the lower realised level after it;
a flat day shows the previous close. `reconcile.low_equity` reads `days.low_open` for that; `days["low"]` stays economic. Only `Main` matches net profit; reconcile at a
window boundary; a cross-check market's leg misses net profit (median up to ~475 $) — check by rank.

## Evidence
**How much the low-curve biases each reader (🔬 2026-10-04, oos1, three populations of 60 / 3,786 / 3,732 strategies):**

| reader | bias | action |
|---|---|---|
| `snoopingScreen` | benchmark 15-26 % oversized; correlation with the asset 0.13-0.28 seen vs 0.32-0.46 real; SPA p 0.72→0.58, 0.95→0.95, 0.79→0.73; StepM names 0 in both | **done 2026-10-04**: reads `equity/closecurve` (0.55 s CPU per strategy) |
| `blindJoint` | same engine, not measured (reads oos2) | **code done 2026-10-04**, never run; waits for the batch's `trades.parquet` |
| CSCV | PBO 0.37→0.35, 0.36→0.39, 0.40→0.52 (measured on populations, not on a variant batch) | rebuild needs trades per variant (SQX export at step 16.5) |
| decay / `degradacion_t` | t = 0.78-0.88× the close-based t; passing 1.65: 19 vs 83 and 63 vs 127; order unchanged (ρ 0.99) | do not rebuild: judge on `drift_excess_t` |
| WFC | **does not read the curve** | none |
| exposure | Sharpe 0.97-1.00× | document only |
| `worst_day_r` | 0.99-1.00× the real daily loss | document only |

Evidence: `AlgoData/scratch/null-fpr-2026-10-04/` `b1_curves.py`, `b2_stats.py`, `b2_all_populations.csv`,
`b2_Test_Calib_USDJPY_H1_momentumL.csv`, `b2_Test_Calib_USA500_H1_pullbackL_rnd.csv`,
`b2_Test_USDJPY_donchianUpperCrossUp_H1.csv`, logs `b2_usdjpy.log`, `b2_usa500.log`.

- 🔬 2026-09-30, the archived USDJPY M30 strategy `4d679e…/2026-09-28T0919` (2,094 long trades,
  `USDJPY_DukasM1_the5ers`, clock Asia/Jerusalem): rebuilt day low = previous day's closing equity
  + the day's worst minute (wicks, window entry … exit − 1) against `harvest/equity.parquet`:
  build 2,667 days and oos1 1,316 days **100 % within 1 $ (max 0.16 $)**; the same days' MTM close
  match only 45 % (median gap 81 $), the previous day's close 45 %. Daily P&L from its differences
  correlates 0.45 with the rebuilt MTM P&L. Golden: `tests/test_portfolio_universe.py`.
  🔬 2026-10-04: on today's EETUS bars it reads 96.7 % — the clock alone; `clock.reclock` to Asia/Jerusalem
  gives 100 % back; today's card point value (631.34, not the trades' 653.92) would read 45 %
  (`export/archived-trades-vs-reclocked-bars`).
  The first point shows it: day 2008-01-02 reads −1,198.27 = that day's trade's `MAE ($)`, the next
  day −376.79 = its `Profit/Loss`. ⚠ Readers that difference this curve as daily P&L (the variant
  batches' `equity.parquet` in CSCV) read low-to-low changes — `OPEN.md` #88.
- ⚠ Superseded reading, kept for its numbers: the rows below took the curve for a mark to market
  with day D = equity carried into D; the correlations with the asset they report are real but
  measure the day's low, not its close.
- Mark-to-market and day stamp (2026-09-25, `XAU_ISOOS_ejemplo` OOS, 115 curves, 2018–2022): one
  strategy's curve changes on 695 days, 390 of them with no trade closing. Median correlation of the
  daily changes with gold: **0.147** sampling the M1 close at the label's instant (00:00), 0.174 at
  −6 h, **0.073** with a plain daily resample (close at the end of D) and falling to 0.04 by +12 h.
  USDJPY_emaCross_H1 is flatter (0.10–0.13 across −12…+12 h) but also peaks at or before the label.
  Was used by `studies/screening/snoopingScreen/inputs.py` until 2026-10-04.
- Format: after `aced0005` header, only Java block-data markers — `0x7a` + 4-byte length, `0x77` +
  1-byte length. Concatenated payload: int count, then count × (big-endian int64 epoch millis,
  big-endian float64). No objects (unlike `orders.bin`).
- Cross-check order in archive: `Results/Portfolio/…`, `Results/Main: …/…`, `Results/AdditionalMarket: …`.
  `P00000` of `Strategy 17.9.39` (XAGUSD check): **10,476 / 35,328 / −24,852** — Portfolio = gold + silver.
- Open position on last bar: at the IS boundary all 962 curves matched stored `Net profit (IS)` within
  **0.59 $**; over full history 172 ran 95–332 $ below (551 OOS trades vs 186 on average).
- 🔬 2026-09-26, USDJPY batch 23-1-53 (`equity_markets.parquet` summed per variant against
  `segments.parquet` NetProfit, `studies/optimisation/marketSurfaces` checks): within 1 $ on
  USDCAD build 100 %, USDCHF 93 %, EURUSD 39 %, EURJPY 15 %, AUDUSD oos1 5 %; gap median 474 $ on
  EURUSD build, max 3,302 $ on GBPUSD. Spearman curve-vs-NetProfit ≥ 0.993 on all 3 mothers × 9
  markets × 2 segments; against the WRONG market it runs −0.4 to +0.6. `equity.json` already counts
  these as `open_at_end`. Mechanism not isolated (swap ruled out: gap uncorrelated with `Commission`).
