---
q: split data=all export into blocks; WFM cells in one CSV; crossTF blocks interleaved not contiguous; Ticket cumcount; assign trade to walk-forward step runFrom runTo; torn_blocks
tag: 🔬  date: 2026-09-23  see: export/data-all-crossmarket, export/wfm-export
---
# `data=all` blocks are not reliably contiguous — split by the separator that fits the kind
- Cross-market: `Symbol`. CrossTF (same symbol): the k-th occurrence of a ticket is block k → `groupby("Ticket").cumcount()`.
- WFM (31 results): cut where `Sample type` turns `IS` → 30 cell blocks (`core/wftrades.chunks()`).
- Assign a trade to a WF step with `searchsorted` over the next step's `runFrom`, never `runFrom <= t <= runTo`.
- `tradestore.pack()` returns `torn_blocks`; non-empty = blocks are guesses.

## Evidence
- CrossTF CSV is sorted by open time with blocks interleaved. Old "new block where ticket stops growing" split one strategy into 173 pieces
  (396 "blocks" for 9 strategies instead of 27); `tradestore.block(packed, s, 0)` returned a sliver, nothing failed.
  Invariant: each block numbers tickets 1..n without gaps. `TestXAU_crossTF`: 9 strategies, 3 blocks each, `max(ticket) == n` in 27, sizes 347 M30 · 180 H1 · 40 H4.
- WFM: `orders.bin` holds main + 30 cells, written in `settings.xml` result order. `XAUUSD/WFM/Strategy 10.16.68`: 60,151 rows.
  Main block `IST`; each cell opens with `IS` (first optimisation window) then `OOS1`, never back.
- `runTo` is midnight → date test drops same-day later trades: 81 of 58,500, 1–2 per step (looks like rounding, is not).
  `searchsorted` vs SQX's `oos_NumberOfTrades` for all 30 cells: 0 discrepancies in 39,873 trades; `core/wftrades.check()` writes the comparison.
- One command: `python3 -m sqx.export.export_wfm --project XAUUSD --databank WFM`.
