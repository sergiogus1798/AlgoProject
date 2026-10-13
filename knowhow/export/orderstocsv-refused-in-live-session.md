---
q: Why does an export fail with «REFUSING: another sqcli already holds» inside a live GUI session?
kw: REFUSING another sqcli already holds, orderstocsv live session, harvest fails live, afterrun --live exit 1, collect.py exportdrv, export from memory, AlgoBank .abk, AlgoTrades deleted
tag: 🔬  date: 2026-10-13  see: perf/algobank-vs-algotrades-vs-orderstocsv, export/orderstocsv-no-multi-databank
---
# `orderstocsv` (sqcli) is refused while a live GUI session holds the install: inside a live session every export must come from memory
Trap: any piece that runs `orderstocsv` fails with «REFUSING: another sqcli already holds <install>» (rc 1) while the install's GUI session is up. Trades come from memory (AlgoBank's `.abk`; `memtrades`/AlgoTrades were deleted 2026-10-13): `liverun.export` dumps the stale banks, the harvest, `export_retest` and `export_trades` take them. A bank not taken falls to orderstocsv, which is refused here, so `afterrun --live` exits 1 and `liverun.export` raises with the reason `take` printed. A second call fails identically at once.
Fix: read from memory in a live session; the stopped route works (`afterrun --role conductor`, worker down: 30.8 s first call with one `orderstocsv`, 1.8 s second with none).

## Evidence
- 🔬 conductor, 2026-10-13, encargo 66 live session 3: `liverun.export` (`ui/daemon/launch/liverun.py:32`) wrote trades from memory for Results and OOS (108 each), then `afterrun --live --project … --databank OOS --databank Results` hit the refusal.
