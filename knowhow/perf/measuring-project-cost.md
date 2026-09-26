---
q: how to measure memory of a module with workers, ru_maxrss wrong for children, sample process tree /proc, tracemalloc peak snapshot, memory bandwidth ceiling 16 processes, compare wall clock per unit of work, perf.catalogue
tag: 🔬  date: 2026-09-20  see: perf/python-parallelism, perf/server-cores-and-ram, perf/process-pool-shutdown
---
# Measure the process tree, at the peak, per unit of work
- Memory with workers: sample the whole tree from `/proc/<pid>/stat` (a floor: 50 ms sampling misses short peaks); `ru_maxrss` is useless
  (`RUSAGE_CHILDREN` = largest single child, `RUSAGE_SELF` = parent only). For `fork` pools sum PSS, not RSS (`perf/python-parallelism`).
- `tracemalloc`: keep the snapshot from the moment the traced total peaked (watcher thread), not after the call.
- Compare between dates per unit of work, never wall clock (exports grow; `history.csv` stores the scale).
Instruments and catalogue: `perf/README.md`, `docs/manual/03-datos-costes-y-registro.pdf` (cap. 12-rendimiento).

## Evidence
- `montecarlo.analyse`, 1 strategy, 5,000 sims: 535 MB by `ru_maxrss`, 2,340 MB by tree sampling.
- First `perf/measure/runner.py` reported every allocation site at 0.0 MB (post-call snapshot).
- STREAM triad: cache-resident scales to 575 GB/s at 96 procs and rising; DRAM-resident flat at 57 GB/s from 16 procs.
  `python3 -m perf.catalogue --scaling`.
