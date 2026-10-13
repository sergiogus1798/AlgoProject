---
q: Why does marketSurfaces take 30+ s per mother at step 18.5 when two mothers run side by side?
kw: OpenBLAS 64 threads, OPENBLAS_NUM_THREADS, threadpool_limits, oversubscription, one.measure slow, blind.py two mothers, BLAS contention
tag: 🔬  date: 2026-10-12  see: perf/python-parallelism
---
# Two study subprocesses side by side each open OpenBLAS at 64 threads
`pipeline/autopilot/blind.py:102-105` runs one mother per thread; each subprocess reaches `marketSurfaces/report.py:97` (`one.measure`, `c @ gross` at `measure/reading.py:70`) with OpenBLAS unbounded. `fanout.run` caps threads only inside the fan-out. Fix, NOT yet in code: `with threadpool_limits(1):` around `one.measure`, or `OPENBLAS_NUM_THREADS=1` in `ui/daemon/launch/chain.py:93`.

## Evidence
- 🔬 `one.measure`, USATEC batch, 4 cores: alone 3.1 s (CPU 11.8); two together 33 s each (CPU 58); two with `OPENBLAS_NUM_THREADS=1` 4.1 s each; two on 2 own cores each 3.7 s.
- 🤔 Production match: `summary.segundos` is 9.0 s for one mother (DAX) and 32-42 s with two (NIKKEI, USATEC). Not reproducible with 96 cores (test limited to 4).
- Source: `findings-P6.md` finding 1.
