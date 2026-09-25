---
q: exit types Close type in XAUUSD corpus; any stop loss take profit; long only; path-independent exits; M1 bar library size load time flat bars OHLC consistency
tag: 🔬  date: 2026-09-24  see: export/fill-and-pricing, export/bars, export/trade-export-columns
---
# XAUUSD corpus exits are 3 types, none a stop; the M1 library loads whole in 0.4 s
- `Close type` ∈ {`Exit After X Bars`, `Exit Signal`, `End Of Friday (Time)`}; no SL/TP; 100 % `Buy`. Delay analyses holding exits fixed are legitimate here.
- ⚠️ Property of these templates, not the world: a population with barriers needs intrabar convention calibration first.
- M1 library: read whole, no mmap/chunking needed. OHLC-consistent; open issue is flat bars → `docs/encargos/17-calidad-del-feed.md`.

## Evidence
- `XAUUSD/MC_Trades`, 960,705 trades: `Exit After X Bars` 720,874 (75.04 %), `Exit Signal` 187,853 (19.55 %), `End Of Friday (Time)` 51,978 (5.41 %).
  95 of 757 strategies never use `Exit Signal` (100 % path-independent exits); 352 use it on < 10 % of trades.
  `raw/XAUUSD/MC_Trades/2026-09-19, deleted 2026-09-25/trades.parquet`: 960,705 trades, 757 strategies (counted 2026-09-25).
- `XAUUSD_DukasM1_Infinox`: 7,949,285 bars (2003-05-05 → 2026-09-22), `core.barstore.source` loads all in 0.4 s. 0 OHLC-inconsistent
  (`H < max(O,C)`, `L > min(O,C)`, `H < L`); 40,097 (0.50 %) flat `High == Low`.
- Consistent with `strategies/CLAUDE.md` on the generated population. Used by `strategies/entryQuality/`, `strategies/profitShape/`.
