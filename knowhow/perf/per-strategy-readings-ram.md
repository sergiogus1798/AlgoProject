---
q: profitShape entryQuality over a whole population; one process per strategy loads the whole trades.parquet; RAM per process; how many in parallel; out of memory session killed; 5000 strategies how long
tag: 🔬  date: 2026-10-01  see: perf/ram-budget
---
# profitShape / entryQuality cost 1.7 GB and ~3 s per strategy: at most 8-12 side by side
Each `--strategy` run loads the population's whole `trades.parquet` (≈1 M rows for 5,000 strategies) and uses ~30 CPU-seconds on
many threads. 64 at once asked for ~110 GB and the OOM killer took the session and a custodian mid-stop (2026-10-01).
Over a whole population use a random subsample, or cap the fan-out at 8-12 and the library threads at 2.

## Evidence
- `/usr/bin/time`: max RSS 1,747 MB (profitShape), 1,735 MB (entryQuality), `Test_Calib_USDJPY_H1/OOS`, 5,026 strategies, 957,949 trades.
- 96 strategies at width 32: 46 s. 500 at width 12 with `POLARS_MAX_THREADS=2 OMP_NUM_THREADS=2`: 279 s and 242 s.
- Full population of 5,026 at width 12: ~45 min per study (extrapolated).
