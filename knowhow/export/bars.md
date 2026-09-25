---
q: export OHLC bars from SQX; data action=export symbol name timeframe; Symbol not found; sync_bars check feeds; bar library M1
tag: 🔬  date: 2026-09-24  see: export/what-a-project-stores, export/exits-and-m1-library
---
# Export bars with the bare symbol and a separate timeframe, one timeframe per JVM
`-data action=export symbols=XAUUSD_DukasM1_Infinox timeframe=<TF> ...` — not `..._M30` (fails `Symbol ... not found.`).
Output `<symbol>-<TF>-No Session.csv`; a second export in the same JVM overwrites (`-run file=cmds.txt` names both the same).
Library refresh: `python3 -m sqx.export.sync_bars --check`; feed list = `assetdata.symbols()` + `markets(symbol)`.

## Evidence
- `sync_bars.wanted()` read `markets.FILE`, removed when `studies/transfer/crossmarket/inputs/markets.py` began delegating to `core.assets` → `AttributeError`; fixed 2026-09-24.
- 📓 2026-09-24: 13 feeds to fetch (~110 M M1 bars): ten the5ers pairs, plus XAGUSD, XAUUSD, Brent (grown in SQX).
  USDJPY fetched: 8,734,300 M1 bars, 2003-05-05 → 2026-09-22, 139 MB Parquet.
