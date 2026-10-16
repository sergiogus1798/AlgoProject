---
q: How do I export bars from SQX: which symbol form and how many timeframes per JVM?
kw: export OHLC bars from SQX; data action=export symbol name timeframe; Symbol not found; sync_bars check feeds; bar library M1; feed price increment vs tick_size
tag: 🔬  date: 2026-10-16  see: export/what-a-project-stores, export/exits-and-m1-library
---
# Export bars with the bare symbol and a separate timeframe, one timeframe per JVM
`-data action=export symbols=XAUUSD_M1 timeframe=<TF> ...` — not `..._M30` (fails `Symbol ... not found.`).
Output `<symbol>-<TF>-No Session.csv`; a second export in the same JVM overwrites (`-run file=cmds.txt` names both the same).
Library refresh: `python3 -m sqx.export.sync_bars --check`; it decodes SQX's own `<feed>_M1.dat` (`core.tickfile.bars`), no export and no JVM; feed list = `assetdata.symbols()` + `markets(symbol)`.
⚠️ A feed's price step is its smallest close-to-close move, not `assets/` `tick_size`: the Dukascopy forex feeds quote a tenth of SQX's tick (EURUSD 0.00001, USDJPY 0.001) → `research/m1-feed-anomaly-statistics`.

## Evidence
- 🔬 2026-10-16: the SQX export had rounded XAUUSD, DAX40, DJ30, NIKKEI225, USA500, USATEC, AUS200, HK50 and UK100 to 2 decimals while their `.dat` carries 3 (XAUUSD: 93.6 % of bars differed, max 0.005); `price_rounding: tick` reproduces SQX's trade costs exactly on build/oos1/oos2 only with the 3-decimal bars. The library is now filled from the `.dat`; its Volume is the `.dat`'s sixth field ÷ 10^5 (equals the export's on 99.9996 %).
- `sync_bars.wanted()` read `markets.FILE`, removed when `studies/transfer/crossmarket/inputs/markets.py` began delegating to `core.assets` → `AttributeError`; fixed 2026-09-24.
- 📓 2026-09-24: 13 feeds to fetch (~110 M M1 bars): ten the5ers pairs, plus XAGUSD, XAUUSD, Brent (grown in SQX).
  USDJPY fetched: 8,734,300 M1 bars, 2003-05-05 → 2026-09-22, 139 MB Parquet.
