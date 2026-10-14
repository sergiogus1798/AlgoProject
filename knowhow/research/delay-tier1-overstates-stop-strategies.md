---
q: Can the delay cost of a strategy with a stop be read with exits held fixed (tier 1)?
kw: entry delay; late entry cost; tier 1 tier 2; given_up; exits fixed; stop recomputed from shifted entry; latency; replay; entryQuality delay wrong for stops
tag: 🔬  date: 2026-10-14  see: export/fill-and-pricing, export/sqx-atr-is-wilder
---
# No: holding a stop's exit fixed overstates the delayed P&L — by 20-45 $ a trade on NIKKEI simpleL, more than half its edge
- Tier 2 (`engines.market.replay`, stop recomputed from the new fill and ATR) on oos1 of seven stop harvests, mean net per trade, SQX → tier 1 → tier 2 at d = 1 bar: simpleL_fin 45.3 → 42.0 → 27.0; simpleL_auto 34.5 → 36.7 → 15.5; volatilidadL 53.0 → 50.1 → 46.2; USA500 indicesIBS 44.2 → 37.0 → 9.7; USDJPY doubleROC 8.1 → 3.1 → −0.3.
- Tier 1 even reads a 2-bar delay as a gain (simpleL 34.5 → 50.9): the old stop price is kept while the entry moved.
- Under tier 2, signals whose result survives a late entry (volatilidadL −13 %) separate from those that do not (simpleL −40 to −100 %).
- Dropped trades 0-7 %, unknown exits 0.2-7 %: small enough that tier 2 is the reliable one for stop strategies; tier 1 stays right only without stops.

## Evidence
Scratch run of 2026-10-14 over `AlgoData/harvest/*/Stop_p90/*` (sample OOS, `Deleted` excluded), P&L by
`engines.market.reprice.pnl` at the oos1 card, `walk.replay(..., delay, latency=False)`; d = 1-3, full latency too.
