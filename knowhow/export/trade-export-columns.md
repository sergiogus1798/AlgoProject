---
q: which trade export columns can be dropped; Ticket Balance Time in trade Comment Symbol derivable; Close type needed; trade parquet packing size speed memory; categorical columns
tag: 🔬  date: 2026-09-21  see: export/orderstocsv-schema, export/storage-format
---
# Of 16 trade columns, 12 carry everything; Ticket/Time in trade/Comment/Symbol are derivable
- Drop `Ticket` only if the file passes `tradestore.ordered()` (open-time sorted, no dup open times, no overlaps); else keep it.
- Drop `Symbol` only under `data=main`; under `data=all` it is the sole market separator (`tradestore.pack(per_market=True)` keeps it).
- `Balance` is derivable but kept (owner's decision). `Close type` is NOT disposable.
- Keep packed text columns categorical. Per-strategy work: read once, split with `tradestore.by_strategy()`.

## Evidence
Measured on `Strategy 1.19.29` (763 trades), 5 XAUUSD strategies (4,115 trades), re-verified on 757 strategies / 960,705 trades, zero discrepancies.

| dropped | why |
|---|---|
| `Ticket` | = row index + 1; sort by (`Open time`,`Close time`) reproduces it; Parquet keeps row order |
| `Time in trade` | = Close − Open, stored as text (`"2h 0m"`), 26 distinct values |
| `Comment` | 763 of 763 null |
| `Symbol` | constant per file → manifest |

- `Balance = 100,000 + cumsum(P/L)`, max deviation 0.17 over 763 rows (rounding, not a fee).
- `Close type`: `Exit Signal` 662 / `Exit After X Bars` 83 / `End Of Friday (Time)` 18 — moves with parameters; parameter-surface studies need it.
- `ordered()` failures on 757-strategy XAUUSD fleet: zero (single-position throughout). Pyramiding / two entries same bar would fail.
- Packing: 179 MB CSV → 20.5 MB zstd Parquet (8.7×). Read all 960,705 trades 0.16 s vs ~3.9 s CSVs; one strategy 0.032 s vs 0.005 s own CSV (filter scans file).
- Memory trade: monteCarlo load 5.2 s / 266 MB peak RSS (CSVs) → 1.0 s / ~620 MB (Parquet). Frames 74 MB vs 406 MB, but Arrow
  decompression ~270 MB transient RSS; `to_pandas(split_blocks=True, self_destruct=True)` recovers only 30 MB. Memory-bound readers: `tradestore.read(path, name)`.
- ⚠️ Object text columns: 326 MB vs 74 MB categorical. `core.trades.cost()` does `.astype("object").map(SIDE)` on `Type` — mapping a categorical returns a categorical that refuses to multiply.
