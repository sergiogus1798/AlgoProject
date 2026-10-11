---
q: Why does step 18.5 fail with «trades the common repricer cannot fill» only on the last day of oos2?
kw: trades the common repricer cannot fill; a stamp that is no bar's; EndTest; first at 2026-09-30; marketSurfaces oos2; sync_bars; bar library stale; barstore.library to; weekly-data-update
tag: 🔬  date: 2026-10-10  see: export/off-grid-stamps-and-stop-exits, pipeline/variant-batch-refused-on-negative-zero
---
# Python's M1 bar library was behind SQX's data, so trades closing after its last bar had no bar
Trap: `bin/weekly-data-update.sh` refreshed SQX's data and the dates of `assets/_policy.yaml` but never
ran `python3 -m sqx.export.sync_bars`. SQX then trades up to the end of `oos2`, the library
(`core.barstore`, `AlgoData/bars`) stops earlier, and `engines.market.reprice.located` returns -1 for every
close after the library's last bar (one `EndTest` per variant plus the last exits); the blind reading
dies, the one without oos2 passes. Seen on XAUUSD, XAGUSD, HK50 (library to 2026-09-30 02:00).
Check: `python3 -m sqx.export.sync_bars --check` (PULL = stale), or `core.barstore.library()[feed]["to"]`
against the asset's `oos2.to`. Fix: `python3 -m sqx.export.sync_bars` (one worker start per feed); the weekly update runs it as step 5.

## Evidence
Test_USA500_H1_tendencia_wf1, run 20261010-194403, step 18.5 blind: 1,001 trades of mother 20.17.293 on
XAUUSD_M1 (832 EndTest at 23:00, 172 Exit After X Bars at 22:00/23:00), bars' last H1 2026-09-30 02:00.
All 27 feeds were behind `_policy.yaml`'s `data.to` (library 09-30..10-02, policy 10-09).
