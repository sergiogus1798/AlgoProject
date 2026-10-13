---
q: Why is a databank's .sqx no longer byte-identical to my snapshot after SQX ran, and is anything lost?
kw: byte-identical snapshot, cmp differs after exit, rewrites every loaded strategy, saved with no change, Retester/Results bytes, snapshot compare
tag: 🔬  date: 2026-10-13  see: sync-deletes-unloaded-files, sqx-format/strategy-identity
---
# SQX rewrites every loaded strategy at a sync or at exit, even unchanged: bytes differ, content does not
Trap: comparing a snapshot with `cmp`/checksums after any session that loaded the bank. Compare file
count, names, `identity()`, the (result, sample) stat blocks, statistic values and `orders.bin` instead.
Those stay equal; the zip bytes do not (a clean 10,000-strategy sync logs 10,000 «saved»).

## Evidence
- 🔬 2026-10-13, conductor `Retester/Results` (17 files) vs `AlgoData/snapshots/conductor-2026-10-13-encargo66`: same count and names,
  bytes differ; identity, statistics and orders equal on 17/17. Sessions 1 and 2 of encargo 66 (`cmp_sqx.py` in `/dev/shm/tmp66/live2/`).
