---
q: Why does orderstocsv take minutes per databank, and what writes the same trade CSVs in seconds?
kw: orderstocsv slow, export.trades dead time, 274 s per 1000 strategies, DataManager.getDataInfo per row, OpenPrice ClosePrice column snippet, AlgoTrades deleted, AlgoBank, export from memory, live session export, float price 761.1500244140625
tag: 🔬  date: 2026-10-12  see: export-after-every-stop
---
# orderstocsv's time is two price columns asking DataManager on every row; from memory the same trades take seconds (AlgoBank)
orderstocsv's `OpenPrice` and `ClosePrice` columns call `DataManager.getDataInfo("History",
symbol)` **per row**: 237 of the 245 s of a 1,000-strategy databank. A snippet that reads the
strategies a live session holds and looks the decimals up once wrote the same CSVs in 3.9 s
against 274 on `Results`, 1.4 against 136 on `OOS`, 2,000 files byte-identical. That snippet
(`AlgoTrades`) was deleted 2026-10-13 with `memtrades`: `AlgoBank` (`.abk`) carries the trades
now and orderstocsv is the route of a stopped install only.

## Evidence
- 🔬 conductor, 2026-10-12, databanks copied from `Test_XAUUSD_H1_ruptura_mcptS`: per-column
  timing inside the snippet, `cmp` of every CSV against orderstocsv's: 1,000 strategies XAUUSD H1,
  `Results` (392,890 trades) 274 s against 3.9 s, `OOS` 136 s against 1.4 s.
- 🔬 same day, live route end to end: `liverun.export` 19 s for both databanks, `trades.parquet`
  equal to the reference's (392,890 rows).
- 📓 a real run's `tiempos.md`: export.trades 187 + 97 s beside 1,216 s of SQX.
- `parallelStream` over the strategies was 3.6× slower than the plain loop — do not retry it.
- Trap, price formatting outside SQX's snippet: `Order.OpenPrice` is a `float`; widened to
  `double` before `SQUtils.d2String` it prints `761.1500244140625` for `761.15`.
- `-tools action=orderstocsv` starts a second JVM and loads every `.sqx` from disk; only
  `data=main`/`all` trade lists, metrics never come from it.
