---
q: parse dailyEquity.bin, daily equity curve without SQX, sub-period / split OOS study, which dailyEquity.bin (Main vs Portfolio vs AdditionalMarket), equity vs net profit mismatch, open position last bar
tag: 🔬  date: 2026-09-22  see: sqx-format/result-sections, sqx-format/sqx-zip-members
---
# dailyEquity.bin parses: cumulative P&L per trading day; take `Main`, reconcile at window boundaries
`core/sqxstats.equity(path, result="Main")` reads it. Value = **cumulative P&L in account currency**
(not balance), one point per calendar trading day. With a cross-check the `.sqx` holds several
curves (`Portfolio`, `Main: …`, `AdditionalMarket: …`) — only `Main` matches the databank's net profit.
Reconcile a curve at a window boundary, never at end of file; drop the last period when aggregating.

## Evidence
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
