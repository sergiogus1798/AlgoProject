---
q: parse dailyEquity.bin, daily equity curve without SQX, sub-period / split OOS study, which dailyEquity.bin (Main vs Portfolio vs AdditionalMarket), equity vs net profit mismatch, open position last bar, is daily equity mark-to-market, which day is the equity stamped, align equity with bars / benchmark
tag: 🔬  date: 2026-09-25  see: sqx-format/result-sections, sqx-format/sqx-zip-members
---
# dailyEquity.bin parses: cumulative P&L per trading day; take `Main`, reconcile at window boundaries
`core/sqxstats.equity(path, result="Main")` reads it. Value = **cumulative P&L in account currency**
(not balance), one point per calendar trading day. With a cross-check the `.sqx` holds several
curves (`Portfolio`, `Main: …`, `AdditionalMarket: …`) — only `Main` matches the databank's net profit.
Reconcile a curve at a window boundary, never at end of file; drop the last period when aggregating.
It is **marked to market** (it moves on days nothing closed), and **day D holds the equity carried
into D**, not the one D ended with: to set a price series beside it, sample the close at each
label's own instant, never `resample("D").last()`, which lags the price one day behind.

## Evidence
- Mark-to-market and day stamp (2026-09-25, `XAU_ISOOS_ejemplo` OOS, 115 curves, 2018–2022): one
  strategy's curve changes on 695 days, 390 of them with no trade closing. Median correlation of the
  daily changes with gold: **0.147** sampling the M1 close at the label's instant (00:00), 0.174 at
  −6 h, **0.073** with a plain daily resample (close at the end of D) and falling to 0.04 by +12 h.
  USDJPY_emaCross_H1 is flatter (0.10–0.13 across −12…+12 h) but also peaks at or before the label.
  Used by `studies/screening/snoopingScreen/inputs.py`.
- Format: after `aced0005` header, only Java block-data markers — `0x7a` + 4-byte length, `0x77` +
  1-byte length. Concatenated payload: int count, then count × (big-endian int64 epoch millis,
  big-endian float64). No objects (unlike `orders.bin`).
- `XAUUSD/OOS`: 3,946 points per strategy, 2007-11-02 → 2022-12-29.
- Enables arbitrary sub-periods; SQX's own sample types are only IS/OOS/full (splitting the OOS in
  two is impossible via any export).
- Cross-check order in archive: `Results/Portfolio/…`, `Results/Main: XAUUSD_DukasM1_Infinox_LOM_M30/…`,
  `Results/AdditionalMarket: XAGUSD_…/…`. `P00000` (variants of `Strategy 17.9.39`, XAGUSD check):
  final **10,476 / 35,328 / −24,852** — Portfolio = gold + silver. Taking the first member silently
  studies a two-market portfolio.
- Open position on last bar: at the IS boundary all 962 curves matched stored `Net profit (IS)` within
  **0.59 $** (float32 vs 2-decimal panel); over full history 172 ran 95–332 $ below. Those 172 average
  **551 OOS trades vs 186** — SQX marks the open position to market in the curve, net profit counts
  only closed trades.
