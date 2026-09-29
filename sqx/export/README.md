# sqx/export — get data out of SQX

Every script here writes into the data root and leaves a `manifest.json` next to what it wrote.
Nothing here writes into the repo. **They have different lifecycles**: `export_metrics.py` keeps one
current CSV per databank and deletes the previous one before writing, `export_trades.py` and
`export_retest.py` write dated, immutable directories, and `sync_bars.py` overwrites one M1 file per
feed because bars are a fact about the market, not about a run. See `studies/CLAUDE.md` for why.

| file | what it does | run it |
|---|---|---|
| `export_metrics.py` | One row per strategy, the view's columns tagged (IS)/(OOS), read off each `.sqx` with no SQX running (`core/sqxview.py`). Replaces the databank's previous export | `python3 -m sqx.export.export_metrics --project XAUUSD --databank OOS` |
| `export_wfm.py` | Everything a Walk-Forward Matrix cross-check stored, as Parquet: one row per cell, one per walk-forward step with paired IS/OOS statistics, the parameters each step settled on (wide), and every trade tagged with its cell and step in one `trades.parquet`. Deletes its intermediates once the split reconciles | `python3 -m sqx.export.export_wfm --project XAUUSD --databank WFM` |
| `export_trades.py` | Every trade of every strategy in a databank, packed into one typed `trades.parquet`. Exports no bars: those live once in the M1 library. Nothing but the Parquet, the manifest and `identity.csv` (strategy, identity — `sign()`, read by `core.study.identity.from_export`) outlives the export | `python3 -m sqx.export.export_trades --project XAUUSD --databank OOS --symbol XAUUSD_DukasM1_Infinox` |
| `export_retest.py` | A cross-market retest databank exported with `data=all`, packed into one `trades.parquet` whose `Symbol` column separates the markets (`tradestore.market()` reads one strategy on one market). Repeat `--databank` to export several — the three WFC legs — with one SQX start, each into its own directory, with an `identity.csv` (strategy, identity; `export_trades.sign`): a retest databank is never harvested, and this file is what signs a crossmarket result once the project is retired — the staged `.sqx` are deleted. `--batch <tag>` (e.g. `structure`, `stopgrid`) nests the export under that tag so two steps retesting the same databank the same day — 23 and 24 — do not overwrite each other's `trades.parquet` (`core.paths.export_dir`, OPEN #74) | `python3 -m sqx.export.export_retest --project XAUUSD --databank WFC_Build --databank WFC_OOS1 --databank WFC_OOS2 --batch structure` |
| `spp_table.py` | The SPP permutation table: one strategy's rows built in its worker, spilled, then streamed into one Parquet under a single schema | imported by `export_spp` |
| `export_spp.py` | Every Sys. Param Permutation profile in a databank, as Parquet: run counts, medians against the original values, the histograms bin by bin, and — where SQX kept them — `spp.parquet`, one row per permutation with its parameters as columns and its 152 statistics beside them. Reads the `.sqx` directly — drives nothing; 16 processes, the permutation table spilled per strategy and streamed | `python3 -m sqx.export.export_spp --project XAUUSD --databank "SPP IS"` |
| `sync_bars.py` | Keep the M1 bar library in step with SQX: pull the feeds assets/_markets.yaml declares that are missing, refresh the ones SQX has grown, and leave every other timeframe to be resampled | `python3 -m sqx.export.sync_bars --check` |
| `archive_logs.py` | Copy both installs' logs to `AlgoData/logs/` as `.gz` before SQX prunes them | `python3 -m sqx.export.archive_logs` |

`export_spp.py` and `archive_logs.py` are the exceptions to the paragraph below: they only read files, drive no instance,
and are safe while the GUI is up. SQX keeps 14 days of logs and deletes the rest on start, so this has
to run more often than that — `OPEN.md` issue 6. Single-day logs reach several GB, so it streams.

The two exporters drive the worker, never the master: `-databank action=export` only works on the instance holding
the project, and the master's CLI is dead while its GUI is up. `core/exportdrv.py` does the staging
and `core/worker.py` waits for the two asynchronous loading steps that otherwise produce a
header-only CSV with no error. Read `knowhow/export/` before changing either script.
