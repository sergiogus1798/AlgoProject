---
q: How can refreshing SQX's bar data (new bars) be automated, and what stays the owner's button?
kw: update SQX bar data download; data action=update on worker lost; master to worker rsync user/data; core.assets --dataranges refresh data ranges
tag: 🔬  date: 2026-10-02  see: costs/tick-feed-coverage, databanks/snapshot-before-restart
---
# Downloading new bars is the owner's button on the master; automate only the read side
- A download on a worker is lost: next worker start overwrites its H2 databases with the master's stale copy.
- Master download = `sqcli` on the master → forbidden while its GUI is up (hard rule 2), snapshot `user/projects` first (hard rule 1). The master counts as running when anything runs out of its folder, a headless `./sqcli` included, not only the GUI window: test with `core.worker.holding(MASTER)`, never `pgrep -f "$MASTER/"` (the command line of `./sqcli` names no folder).
- Safe any time: `python3 -m core.assets --dataranges` asks the conductor and rewrites the `data:` line of all 17 assets in `assets/_policy.yaml`. ⚠️ A stale `data.to` is not a feed the update skips: a rename keeps a feed's bars; a zone change re-downloads them. So after a mass rename the feeds that only changed name stay at the last update's date while the re-downloaded ones are days fresher — a stale feed there is not a feed the update skips. `-data action=update` takes its list from `data.db`'s `DATA` table (`SOURCE` 2 Dukascopy M1, 4 Darwinex ticks, 5 SQ), whatever the feed is called: a dot in the name (`UKOIL.cash_M1`) changes nothing.
- ⚠️ `-symbol action=delete` on a feed that is downloading does NOT stop its job: it kept requesting Dukascopy for hours and its 429s starved every later Dukascopy download (HK50, 2026-10-01). Only `-exit` and a fresh `sqcli` ends it. Run one Dukascopy download at a time; Darwinex is not rate-limited the same way.
- Darwinex's catalogue is `internal/plugins/DataSourceDarwinex/darwinex.csv` (327 symbols): WTI is `XTIUSD`, there is no Brent and no HK50.
- Dukascopy's catalogue is `internal/plugins/DataSourceDukascopy/dukascopy.csv` (753 rows: symbol, name, class, first M1 and tick day): copper is `COPPERCMDUSD` in USD per lb (FTMO's `XCUUSD` is cents per lb, ×100); bonds, platinum, softs and the dollar index only start in 2017-2021.
- Dukascopy throttles by volume, not by count: two M1 feeds back to back took 8 min each, the third crawled on connect timeouts (340 KB in 17 min). Queue Darwinex ticks meanwhile — they run in parallel on the same instance.

## Evidence
- The oos2 roll is per asset: a stale feed stays behind alone (exit 1, alert), and every later Saturday retries it at the same end date (`bin/monthly-oos2-roll.sh`, since 2026-10-03).
- 🔬 2026-10-03, a COPY of the master's `data.db`: `UKOIL.cash_M1` is row ID 347 (`USYMBOL BRENTCMDUSD`, `SOURCE 2`, broker FTMO, EETUS, `DATETO` 2026-09-24, 4,121,895 rows) — the old `BRENTCMDUSD_ftmo`, renamed on 2026-10-01 (`assets/_feed_renames.yaml`), its `.dat` last written 2026-09-26 03:11 by the weekly update (log line «BRENTCMDUSD_ftmo, Completed in 3secs»). `USOIL.cash_M1` is ID 351, created 2026-10-01 08:47 (`LIGHTCMDUSD`), `DATETO` 2026-10-01. Ten feeds still end 2026-09-24, fifty end 09-30/10-01: the re-downloads.
- 🔬 2026-10-03 02:00: the master was held by PID 3016224, `./sqcli`, cwd the master, started 2026-10-01 19:56, parent 1. The weekly script's `pgrep` precheck missed it, copied 7,546 `.sqx` and rotated a snapshot; `sqx.data.update` then refused (`holding`), exit 1. The 02:05 roll moved 26 assets to 2026-09-30 and left UKOIL at 2026-08-31.
- 🔬 `sqcli -data action=update` = GUI "Update all"; with no `symbol=` it updates every configured symbol (67, 16 min, 2026-09-25; a feed may 429 a day or two) (beside `import`, `export`, `exportToMT4/5`, `clone`, `timezones`). Verb reference: `internal/web/SQUANT/help.txt` (readable without starting anything).
- `bin/sqx-worker.sh` start runs `rsync -a --exclude='History/' "$MASTER/user/data/" "$WORKER/user/data/"` (flow master → worker). `History` is a shared symlink,
  but the three H2 databases a backtest reads are per-install copies.
- Conductor sees the master's store via the same rsync. Run mid-update, `--dataranges` caught four feeds moving `2026-01-16` → `2026-09-22`, left thirteen alone.
- 🔬 2026-10-02, master headless: AUDNZD_M1 12:08→12:16, UK100_M1 12:16→12:24, AUSIDXAUD from 12:24 `ConnectTimeoutException datafeed.dukascopy.com` per file; AUDNZD Darwinex ticks started 12:41 beside it and grew 280 MB in 4 min.
