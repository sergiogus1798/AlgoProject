# sqx/export — get data out of SQX

Every script here writes into the data root and leaves a `manifest.json` next to what it wrote.
Nothing here writes into the repo. **They have different lifecycles**: `export_metrics.py` keeps one
current CSV per databank and deletes the previous one before writing, `export_trades.py` and
`export_retest.py` write dated, immutable directories, and `export_bars.py` overwrites one file per
feed because bars are a fact about the market, not about a run. See `tasks/CLAUDE.md` for why.

| file | what it does | run it |
|---|---|---|
| `export_metrics.py` | One row per strategy, columns tagged (IS)/(OOS)/(Full) from the view's sample types. Replaces the databank's previous export | `python3 -m sqx.export.export_metrics --project XAUUSD --databank OOS` |
| `export_wfm.py` | Everything a Walk-Forward Matrix cross-check stored: one row per cell, one per walk-forward step with paired IS/OOS statistics, the parameters each step settled on, and the trades split per cell and step | `python3 -m sqx.export.export_wfm --project XAUUSD --databank WFM` |
| `export_trades.py` | Every trade of every strategy in a databank, plus the bars for each timeframe used | `python3 -m sqx.export.export_trades --project XAUUSD --databank OOS --symbol XAUUSD_DukasM1_Infinox` |
| `export_retest.py` | A cross-market retest databank exported with `data=all`, split into one folder of trades per market | `python3 -m sqx.export.export_retest --project XAUUSD --databank RetestMarkets` |
| `export_spp.py` | Every Sys. Param Permutation profile in a databank: run counts, medians against the original values, the histograms bin by bin, and — where SQX kept them — one row per permutation with its parameters and its 152 statistics. Reads the `.sqx` directly — drives nothing | `python3 -m sqx.export.export_spp --project XAUUSD --databank "SPP IS"` |
| `export_bars.py` | The bars of every market an asset is retested on, into the shared library `AlgoData/bars/<feed>/<TF>.csv` | `python3 -m sqx.export.export_bars --asset XAUUSD` |
| `archive_logs.py` | Copy both installs' logs to `AlgoData/logs/` as `.gz` before SQX prunes them | `python3 -m sqx.export.archive_logs` |

`export_spp.py` and `archive_logs.py` are the exceptions to the paragraph below: they only read files, drive no instance,
and are safe while the GUI is up. SQX keeps 14 days of logs and deletes the rest on start, so this has
to run more often than that — `OPEN.md` issue 6. Single-day logs reach several GB, so it streams.

The two exporters drive the worker, never the master: `-databank action=export` only works on the instance holding
the project, and the master's CLI is dead while its GUI is up. `core/exportdrv.py` does the staging
and `core/worker.py` waits for the two asynchronous loading steps that otherwise produce a
header-only CSV with no error. Read `knowhow/04-export.md` before changing either script.
