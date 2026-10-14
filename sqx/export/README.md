# sqx/export — get data out of SQX

Every script here writes into the data root and leaves a `manifest.json` next to what it wrote.
Nothing here writes into the repo. **They have different lifecycles**: `export_metrics.py` keeps one
current CSV per databank and deletes the previous one before writing, `export_trades.py` and
`export_retest.py` write dated, immutable directories, and `sync_bars.py` overwrites one M1 file per
feed because bars are a fact about the market, not about a run. See `studies/CLAUDE.md` for why.

| file | what it does | run it |
|---|---|---|
| `archive_logs.py` | Copy SQX's logs into the data root before it prunes them. SQX keeps only 14 days. | `python3 -m sqx.export.archive_logs` |
| `export_metrics.py` | Refresh one databank's metrics export: one row per strategy, paired IS/OOS columns. | `python3 -m sqx.export.export_metrics --project XAUUSD --databank OOS` |
| `export_retest.py` | Export retest databanks as one typed Parquet each, every market inside it, in one SQX start. | `python3 -m sqx.export.export_retest --project XAUUSD --databank WFC_Build --databank WFC_OOS1 --databank WFC_OOS2 --batch <tag>` |
| `export_spp.py` | Export a databank's Sys. Param Permutation profiles: one wide table, the histograms, the counts. | `python3 -m sqx.export.export_spp --project XAUUSD --databank "SPP IS"` |
| `export_trades.py` | Export one databank's trades into the data root, as one typed Parquet per export. | `python3 -m sqx.export.export_trades --project XAUUSD --databank OOS --symbol XAUUSD_M1` |
| `export_wfm.py` | Export everything a Walk-Forward Matrix cross-check stored: cells, steps, parameters, trades. Parquet. | `python3 -m sqx.export.export_wfm --project XAUUSD --databank WFM` |
| `membank.py` | Whole databanks written from a live session's memory by the AlgoBank snippet, one `.abk` each. | imported by the memory exports |
| `spp_table.py` | The SPP permutation table: one row per permutation, streamed to Parquet a strategy at a time. | imported by `export_spp` |
| `sync_bars.py` | Keep the M1 bar library in step with SQX: pull what is missing, refresh what SQX has grown. | `python3 -m sqx.export.sync_bars --check` |

`export_spp.py` and `archive_logs.py` are the exceptions to the paragraph below: they only read files, drive no instance,
and are safe while the GUI is up. SQX keeps 14 days of logs and deletes the rest on start, so this has
to run more often than that — `OPEN.md` issue 6. Single-day logs reach several GB, so it streams.

The two exporters drive the worker, never the master: `-databank action=export` only works on the instance holding
the project, and the master's CLI is dead while its GUI is up. `core/exportdrv.py` does the staging
and `core/worker.py` waits for the two asynchronous loading steps that otherwise produce a
header-only CSV with no error. Read `knowhow/export/` before changing either script.
