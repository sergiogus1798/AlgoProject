---
q: SQX commission methods SizeBased PercentageBased PerTrade None Stockpicker; commission per side or round turn; computeCommissionsOnOpen; issue 26 percentage commission once or twice
tag: 🔬  date: 2026-09-27  see: costs/per-task-costs, costs/where-the-spread-is, export/orderstocsv-schema
---
# `PercentageBased` is charged ONCE per trade, on the open price: `(pct/100) × size × openPrice × pointValue`
Methods: `None`, `SizeBased`, `PerTrade`, `PercentageBased`, `Stockpicker`. Both `SizeBased` and `PercentageBased` charge in `computeCommissionsOnOpen`; `computeCommissionsOnClose` returns 0.
🔬 2026-09-27, trade by trade: 100 % of the same-day XAUUSD trades that do not cross the 23:00 rollover match ONE charge on the open to the cent; 0 % match two. A `%` declared in `assets/` is therefore the round-turn cost.
⚠️ The 2026-09-26 "k = 1.87, charged twice" was wrong: its "same-day" subset kept trades crossing 23:00, which carry swap (18–75 $/lot), and a least-squares fit let them drag k. Isolate swap by the rollover hour, never by the calendar date.
🤔 `SizeBased`'s "$16 round turn under `SizeBased 8`" (older note) was never reconciled the same way — redo it with this card's method before relying on it.

## Evidence
Snippet: `internal/extend/Snippets/SQ/Trading/Commissions/PercentageBased.java` (charges only on open, on `order.getOpenPrice()`).

Harvest `AlgoData/harvest/XAU_ISOOS_ejemplo/Results/2026-09-23/trades.parquet`; project `XAU_ISOOS_ejemplo` on `SQX_w2` carries `PercentageBased CommissionPct=0.001` on both tasks (read from `project.cfx`).
`diff = (Close−Open)·dir·Size·100 − Profit/Loss`, `c = 1e-5·Size·OpenPrice·100`, same-date trades (45,488):

| hypothesis | fits within 0.03 $ |
|---|---|
| 1 × `c` | 96.5 % — and 100 % of those not crossing 23:00 (misses are ±0.015 $ price rounding at larger sizes) |
| 2 × `c` | 0.0 % |
| `c_open + c_close` | 0.0 % |

The 1,583 misfits: 1,566 cross 23:00 (residual 18.8 / 25.5 / 74.6 $ per lot at p10/p50/p90 — swap, triple on Wednesday); the other 17 are ≤ 0.035 $ rounding. Median `diff / c` = 1.000 in IS and OOS alike.
