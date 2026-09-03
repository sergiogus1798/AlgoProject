# 1_sqx/export — get data out of SQX

Both scripts write into the data root (`~/Desktop/AlgoData/raw/...`) and leave a `manifest.json`
next to what they wrote. Nothing here writes into the repo.

| file | what it does | run it |
|---|---|---|
| `export_metrics.py` | One row per strategy, columns tagged (IS)/(OOS)/(Full) from the view's sample types | `python3 1_sqx/export/export_metrics.py --project XAUUSD --databank OOS` |
| `export_trades.py` | Every trade of every strategy in a databank, plus the bars for each timeframe used | `python3 1_sqx/export/export_trades.py --project XAUUSD --databank OOS --symbol XAUUSD_DukasM1_Infinox` |

Both drive the worker, never the master: `-databank action=export` only works on the instance holding
the project, and the master's CLI is dead while its GUI is up. `core/exportdrv.py` does the staging
and `core/worker.py` waits for the two asynchronous loading steps that otherwise produce a
header-only CSV with no error. Read `knowhow/04-export.md` before changing either script.
