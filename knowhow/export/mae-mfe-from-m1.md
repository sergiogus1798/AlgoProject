---
q: rebuild MAE MFE from M1 bars; which minutes SQX counts in a trade's MAE; MAE ($) wick or close; floating equity minute by minute; intraday worst floating for prop-firm daily loss; exit minute excluded; cost of a minute-level floating path
tag: 🔬  date: 2026-09-30  see: export/orderstocsv-schema, export/fill-and-pricing, sqx-format/daily-equity-bin
---
# SQX's MAE/MFE = the M1 wicks from the entry minute to the minute BEFORE the exit, against the fill price
Per trade: `MAE ($) = min(0, side × (worst wick − Open price)) × Size × pointValue` over M1 bars `[open minute, close minute − 1]`
— a long's worst wick is `Low`, its best `High`. The exit minute is **not** counted (exit fills at that bar's open).
Minute **closes** do not reproduce it (median gap 20 $). So the columns give the size of each excursion, the M1 rebuild gives
its minute; the rebuild is licensed by matching the columns first. Cost: under a second per strategy on one core.

## Evidence
- Archived USDJPY M30 strategy `4d679e…/2026-09-28T0919`, 2,094 trades (all long), `USDJPY_DukasM1_the5ers` 8,734,300 bars,
  point value 653.92 by regression; scratch benchmark, 2026-09-30:

  | minutes counted | MAE exact ≤ 1 $ | MFE exact ≤ 1 $ |
  |---|---|---|
  | open … close (inclusive) | 98.42 % | 98.57 % |
  | **open … close − 1** | **100.00 %** | **99.90 %** |
  | open + 1 … close − 1 | 95.61 % | 96.32 % |
  | open + 1 … close | 94.03 % | 94.99 % |

  Minute closes instead of wicks (inclusive window): corr 0.9956, median |gap| 20.16 $, p95 96.58 $ (median |MAE| 407.86 $).
- Timing: read 3 M1 columns 0.55 s; every trade's minute path 0.08 s; daily minimum over 6,218 days 0.16 s; peak RSS 1.2 GB.
  1,078,544 minutes in position (12.3 % of bars).
- 🤔 Not tested: short trades (this strategy has none) — whether a short's worst wick needs the spread added (bars bid, a short
  closes at the ask); a strategy with stops or targets filled inside a bar; feeds other than the5ers USDJPY. The index CFDs
  (DAX40, DJ30, NIKKEI225, USA500, USATEC) have no M1 in `AlgoData/bars/` (listing 2026-09-30).
