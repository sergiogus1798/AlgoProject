---
name: export
description: Export data out of StrategyQuant X — a databank's metrics with IS/OOS columns, every trade of every strategy, or OHLC bars. Use when the owner asks to extract, export or pull data from SQX or a databank.
---

# /export

Everything lands in the data root with a manifest. Read `knowhow/export/` before deviating from
these commands; the traps in it are the reason they look the way they do.

## Metrics — one row per strategy

```bash
python3 -m sqx.export.export_metrics --project XAUUSD --databank OOS   # read off the .sqx, no SQX
```

The columns are the owner's «Export Data View», rebuilt from each file's SQStats
(`core/sqxview.py`, 2026-09-27: equal to the view's export within float32); both sample blocks
come out tagged (IS)/(OOS). No install is started — 100 strategies in half a second.

**A workflow project lives on the custodian** (`/template-run --workflow`): add `--role custodian`
to every export here, or the command looks for the project on the master and finds nothing.

## Trades, and the bars they were taken on

```bash
python3 -m sqx.export.export_trades --project XAUUSD --databank OOS \
    --symbol XAUUSD_M1 [--role custodian]
```

The symbol carries no timeframe suffix. A folder of `.sqx` exports in one JVM start.

## Before you run either

1. **Check `~/Desktop/AlgoData/INDEX.md`.** The export may already exist. Re-exporting a databank is
   minutes of compute and a second copy of the same rows.
2. **Check the databank is on disk.** A databank set to "Auto-sync never" can hold records in memory
   and have an empty directory; a file-based export then silently sees nothing. Look downstream for a
   synced copy — run `sqx/inspect/dump_project.py <PROJECT>` to see which task writes where.
3. **The worker must end stopped.** If a run fails halfway, stop it: `bin/sqx-worker.sh stop`.

## After

Add a row to `~/Desktop/AlgoData/INDEX.md`: date, project, databank, what was exported, row count,
path. That index is how every future session finds the data without listing gigabytes.
