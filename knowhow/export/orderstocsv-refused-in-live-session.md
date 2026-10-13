---
q: Why does an export fail with «REFUSING: another sqcli already holds» inside a live GUI session?
kw: REFUSING another sqcli already holds, orderstocsv live session, harvest fails live, afterrun --live exit 1, collect.py exportdrv, export from memory, AlgoTrades memtrades, AlgoBank
tag: 🔬  date: 2026-10-13  see: perf/algobank-vs-algotrades-vs-orderstocsv, export/orderstocsv-no-multi-databank
---
# `orderstocsv` (sqcli) is refused while a live GUI session holds the install: inside a live session every export must come from memory
Trap: any piece that runs `orderstocsv` fails with «REFUSING: another sqcli already holds <install>» (rc 1) while the install's GUI session is up. Trades can come from memory (`memtrades`, AlgoTrades or AlgoBank); the Results harvest piece (`studies/screening/gate/harvest.py:143` -> `collect.py:153` -> `core/exportdrv.py:39`) cannot, so `afterrun --live` exits 1. A second call fails identically at once.
Fix: read from memory in a live session (snippet); the stopped route works (`afterrun --role conductor`, worker down: 30.8 s first call with one `orderstocsv`, 1.8 s second with none). Moving the harvest to AlgoBank is open (`docs/encargos/66-performance.md`, tanda E).

## Evidence
- 🔬 conductor, 2026-10-13, encargo 66 live session 3: `liverun.export` (`ui/daemon/launch/liverun.py:32`) wrote trades from memory for Results and OOS (108 each), then `afterrun --live --project … --databank OOS --databank Results` hit the refusal.
