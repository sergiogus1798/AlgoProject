---
q: Why does orderstocsv take minutes per databank, and what writes the same trade CSVs in seconds?
kw: orderstocsv slow, export.trades dead time, 274 s per 1000 strategies, DataManager.getDataInfo per row, OpenPrice ClosePrice column snippet, AlgoTrades, memtrades, _trades_mem, _done.tsv, export from memory, live session export, float price 761.1500244140625
tag: 🔬  date: 2026-10-12  see: export-after-every-stop
---
# orderstocsv's time is two price columns asking DataManager on every row; the AlgoTrades snippet writes the same bytes from memory in 4 s
orderstocsv's `OpenPrice` and `ClosePrice` columns call `DataManager.getDataInfo("History",
symbol)` **per row**: 237 of the 245 s of a 1,000-strategy databank. `AlgoTrades`
(`sqx/snippets/`) uses the same column snippets on the strategies a live session holds and looks
the decimals up once: 3.9 s against 274 on `Results`, 1.4 against 136 on `OOS`, 2,000 files
byte-identical. `sqx.export.memtrades` wires it into the live route; orderstocsv stays as the
fallback.

## Evidence
- 🔬 conductor, 2026-10-12, databanks copied from `Test_XAUUSD_H1_ruptura_mcptS`: per-column
  timing inside the snippet, then the table below; `cmp` of every CSV against orderstocsv's.
- 🔬 same day, live route end to end: `liverun.export` 19 s for both databanks, `trades.parquet`
  equal to the reference's (392,890 rows).
- 📓 a real run's `tiempos.md`: export.trades 187 + 97 s beside 1,216 s of SQX.
- `parallelStream` over the strategies was 3.6× slower than the plain loop — do not retry it.

## Also
`-tools action=orderstocsv` starts a second JVM, loads every `.sqx` from disk and formats each
trade with SQX's trade-list column snippets. Two of them, `OpenPrice` and `ClosePrice`, call
`DataManager.getDataInfo("History", symbol)` **per row** to learn the symbol's decimals: 237 of
the 245 s of a 1,000-strategy databank. `AlgoTrades` (`sqx/snippets/`, a CustomAnalysis snippet)
uses the same column snippets on the strategies the live session already holds and looks the
decimals up once per symbol: 3.9 s against 274 on `Results`, 1.4 against 136 on `OOS`, the
2,000 files byte-identical. `sqx.export.memtrades` wires it into the live route, with orderstocsv
as the fallback (below).

| 1,000 strategies, XAUUSD H1 | orderstocsv | AlgoTrades |
|---|---|---|
| `Results` (392,890 trades) | 274 s | 3.9 s |
| `OOS` | 136 s | 1.4 s |

Output is byte-identical on all 2,000 files. `sqx.export.memtrades.run` writes them to
`_trades_mem/` beside the databank's exports while the session is alive (`ui/daemon/launch/
liverun.export`, before the stop); `export_trades` takes them (`memtrades.take`) only when
`_done.tsv` exists, lists exactly the databank's strategies and is newer than its newest `.sqx` —
otherwise orderstocsv runs as before. A stop resaves the `.sqx`, so an export run **after** the
stop always falls back: correct, just slow. Only `data=main` trades are covered; `export_retest`
and `export_wfm` (`data=all`) and the metrics still go through SQX's CLI.

Trap when formatting a price outside SQX's snippet: `Order.OpenPrice` is a `float`; widened to
`double` before `SQUtils.d2String` it prints `761.1500244140625` for `761.15`.
