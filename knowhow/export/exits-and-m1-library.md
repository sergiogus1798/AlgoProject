---
q: What exit types does the XAUUSD MC_Trades corpus use, and are they path-independent?
kw: exit types Close type in XAUUSD corpus; any stop loss take profit; long only; path-independent exits
tag: 🔬  date: 2026-10-11  see: export/fill-and-pricing, export/m1-library-loads-whole, export/bars, export/trade-export-columns
---
# XAUUSD corpus exits are 3 types, none a stop
- `Close type` ∈ {`Exit After X Bars`, `Exit Signal`, `End Of Friday (Time)`}; no SL/TP; 100 % `Buy`. Delay analyses holding exits fixed are legitimate here.
- ⚠️ Property of these templates, not the world: a population with barriers needs intrabar convention calibration first.
- The M1 library that prices them → `export/m1-library-loads-whole`.

## Evidence
- `XAUUSD/MC_Trades`, 960,705 trades: `Exit After X Bars` 720,874 (75.04 %), `Exit Signal` 187,853 (19.55 %), `End Of Friday (Time)` 51,978 (5.41 %).
  95 of 757 strategies never use `Exit Signal` (100 % path-independent exits); 352 use it on < 10 % of trades.
  `raw/XAUUSD/MC_Trades/2026-09-19, deleted 2026-09-25/trades.parquet`: 960,705 trades, 757 strategies (counted 2026-09-25).
- Consistent with `studies/CLAUDE.md` on the generated population. Used by `studies/readings/entryQuality/`, `studies/readings/profitShape/`.
