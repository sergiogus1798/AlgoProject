---
q: does a sync prune a databank nobody opened, unloaded databank safe on restart, removed 0 log, starting a worker for other work endangers batch
tag: 🔬  date: 2026-09-23  see: databanks/sync-deletes-unloaded-files, databanks/snapshot-before-restart
---
# A sync only touches databanks that were loaded; one nobody opened is not pruned
Loss needs a databank **loaded and then emptied or partly filled** (`ClearDatabanks`, partial load).
Another session starting the install for unrelated work does not by itself endanger an unopened
databank. ⚠️ Narrowing, not all-clear: anything that loads then clears still destroys a batch; keep the
no-commands-between-start-and-collect discipline and the snapshot.

## Evidence
Custodian log `SQX_w2/user/log/StrategyQuant/log_2026_09_23.log`:

| evidence | shows |
|---|---|
| 26 `removed` fields all day, every one `removed 0` | nothing pruned across ~9 start/stop cycles |
| 22 `Synchronizing databanks to files`, ~9 `StrategiesSaver` lines | most syncs wrote nothing; with nothing loaded the log shows header + `Synchronization finished.` and no databank line |
| 07:20–07:33 cycles loaded only `bench_smt`, `smoke_keltnerUpperCrossUp` | `Retester/RetestOut` never in memory, kept its **962 `.sqx`** |
| `Retester/RetestOut saved - files before sync 962 / after sync 962 / removed 0 in 21.95 s` (06:48) | the cycle that loaded it round-tripped intact |

The USDJPY `before 248 / after 36 / removed 248` line is a `ClearDatabanks` case, not an untouched sync.
🤔 Not luck (first reading): the files were never pruning candidates.
