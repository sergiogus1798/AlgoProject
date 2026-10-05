---
q: How does SQX compute a trade's MAE and MFE from M1 bars?
kw: rebuild MAE MFE from M1 bars; which minutes SQX counts in a trade's MAE; MAE ($) wick or close; floating equity minute by minute; intraday worst floating for prop-firm daily loss; exit minute excluded; cost of a minute-level floating path; stop loss SL Close time stamped at the bar open; where inside the bar was the stop hit; MAE of a stopped trade; exit bar gap MFE; point value biased by swap; licencia MAE/MFE falla con stop
tag: 🔬  date: 2026-10-05  see: export/orderstocsv-schema, export/fill-and-pricing, sqx-format/daily-equity-bin
---
# SQX's MAE/MFE = the M1 wicks from the entry minute to the minute BEFORE the exit, against the fill price
Per trade: `MAE ($) = min(0, side × (worst wick − Open price)) × Size × pointValue` over M1 bars `[open minute, close minute − 1]`
— a long's worst wick is `Low`, its best `High` — plus the exit minute's **open** (its wicks are not counted). Minute closes
do not reproduce it (median gap 20 $). The columns size each excursion, the M1 rebuild places it; match the columns first.
**With a stop (🔬 2026-10-05):** a `Close type = SL` exit is stamped at the **open of the timeframe bar** it was hit in — the
M1 that reaches `Close price` comes 0–29 min later on M30 (`equity/stopexit.retime`) — and its MAE is its move to `Close
price` itself (`stopexit.fills`). Fit the point value on same-day trades only: overnight P/L carries swap. Cost: < 1 s each.

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
- 🔬 2026-10-05, the 10 NIKKEI225 M30 strategies of `Test_NIKKEI225_M30_simpleL_ref` with the step-24 stop (2,775 trades, 891
  `SL`, all long, `NIKKEI225_M1`): every `SL` close time is on the M30 grid; the first M1 whose `Low` ≤ `Close price` is
  0–29 min after the stamp (quartiles 6 / 12 / 20), and in 50 of 891 no M1 of the bar reaches it (slippage fills beyond the
  wick: the bar's lowest minute is taken). Licence at 1 $ per member, MAE / MFE exact: as the rule above stood 0.47 / 0.48;
  + same-day point value (0.063136 against 0.062922 fitted on all trades, 0.34 % low) and the stop re-timed with its fill as
  the worst point: 0.99–1.00 / 0.97–0.99 (`SL` trades 891 of 891 on both); + the exit minute's open on the other exits (49
  trades whose exit bar gapped past every earlier wick, e.g. MFE 540.35 = move to the 08:00 bar's open 10926.65, the fill
  was 10925.59): **0.99–1.00 / 1.00, 10 of 10 licensed at 0.99**. SQX's daily low curve of a stop version was not on disk
  to check the minute path against (step 24 keeps none).
- 🤔 Not tested: short trades (this strategy has none) — whether a short's worst wick needs the spread added (bars bid, a short
  closes at the ask); a strategy with stops or targets filled inside a bar; feeds other than the5ers USDJPY. The index CFDs
  (DAX40, DJ30, NIKKEI225, USA500, USATEC) have no M1 in `AlgoData/bars/` (listing 2026-09-30).
