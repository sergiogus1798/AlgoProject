---
q: parse dailyEquity.bin, daily equity curve without SQX, sub-period / split OOS study, which dailyEquity.bin (Main vs Portfolio vs AdditionalMarket), equity vs net profit mismatch, open position last bar, cross-check market curve sum vs NetProfit
tag: 🔬  date: 2026-09-26  see: sqx-format/result-sections, sqx-format/leg-curve-warmup
---
# dailyEquity.bin parses: cumulative P&L per trading day; take `Main`, reconcile at window boundaries
`core/sqxstats.equity(path, result="Main")` reads it. Value = **cumulative P&L in account currency**
(not balance), one point per calendar trading day. With a cross-check the `.sqx` holds several
curves (`Portfolio`, `Main: …`, `AdditionalMarket: …`) — only `Main` matches the databank's net profit.
Reconcile a curve at a window boundary, never at end of file; drop the last period when aggregating.
**On a cross-check market's leg the curve's total misses SQX's net profit on most variants** (one-sided,
curve below, median up to ~475 $) — rank the stored `NetProfit`, and check a curve by rank, not dollars.

## Evidence
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
