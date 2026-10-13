---
q: How fast is AlgoBank against AlgoTrades and orderstocsv, and how much /dev/shm does an .abk take?
kw: AlgoBank timing, membank.run seconds, .abk 905 MB per 10,000 strategies, dump folder removed after export, /dev/shm/algobank, 7.27M orders, 73,359 trades, AlgoTrades 2.95 s
tag: 🔬  date: 2026-10-13  see: export/orderstocsv-slow-is-datamanager, export/orderstocsv-no-multi-databank
---
# AlgoBank writes whole databanks in ~1.2 s (100 strategies) and 7.8 s (10,000); `liverun.export` deletes the folder after each export
| case (conductor, live session) | AlgoBank | AlgoTrades | orderstocsv |
|---|---|---|---|
| Results+OOS, 100 strategies, 73,359 trades | 1.15-1.19 s | 2.95 s | 16-27 s per bank |
| 10,000 strategies, 7.27 M orders | 7.8 s (+ 1.5 s load, 4.9 s trades frame) | 38.6 s | - |
| 17 walk-forward strategies, 472,733 orders | ~1 s | - | 168.3 s |

905 MB of `/dev/shm` per 10,000 strategies; `take` consumes each `.abk` and `liverun.export` removes the folder in a `finally`. Rows equal both older routes. AlgoTrades was deleted 2026-10-13 (owner, Q14=A): its column is history.

## Evidence
- 🔬 2026-10-13, encargo 66 live session 2 (`/dev/shm/tmp66/live2/notes.md`): runs 1.19, 1.16, 1.15 s; AlgoTrades 2.95 ×3; 11 live tests pass.
  4 banks of 8 strategies: 1.04-1.11 s vs AlgoTrades 4.5 s. Pass split at 10,000: orders 3.6-4.0 s, stats 0.6, equity 0.1, xml 1.5. Under a running 10,000-strategy build: 24.8 s once.
